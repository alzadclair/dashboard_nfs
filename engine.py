import os
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime

class DataEngineGDrive:
    def __init__(self, storage_path="data_warehouse.parquet", quarantine_path="quarantine.parquet"):
        self.storage_path = storage_path
        self.quarantine_path = quarantine_path
        self.mandatory_cols = ['Número NF', 'CNPJ Fornecedor', 'Data de Emissão', 'Valor Total', 'E-mail do Comprador']

    def generate_hash_id(self, row):
        """Cria chave única invariante para evitar duplicidades no pipeline."""
        raw_key = f"{str(row.get('CNPJ Fornecedor', '')).strip()}_" \
                  f"{str(row.get('Número NF', '')).strip()}_" \
                  f"{str(row.get('Série', '1')).strip()}_" \
                  f"{str(row.get('Valor Total', '')).strip()}"
        return hashlib.md5(raw_key.encode('utf-8')).hexdigest()

    def validate_and_clean(self, df_raw, filename):
        """Aplica regras formais de validação, quarentena e deduplicação."""
        df = df_raw.copy()
        df['UUID_Registro'] = df.apply(self.generate_hash_id, axis=1)
        df['Data_Processamento'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df['Arquivo_Origem'] = filename

        # Flag de Inconsistências
        invalid_mask = pd.Series(False, index=df.index)
        quarantine_reasons = pd.Series("", index=df.index, dtype=str)

        # Rule 1: Campos Obrigatórios Ausentes
        for col in self.mandatory_cols:
            if col in df.columns:
                null_rows = df[col].isnull() | (df[col].astype(str).str.strip() == '')
                invalid_mask |= null_rows
                quarantine_reasons.loc[null_rows] += f"Campo obrigatório ausente: {col}; "
            else:
                invalid_mask |= True
                quarantine_reasons += f"Coluna crítica ausente: {col}; "

        # Rule 2: Formato de Valores Numéricos e Datas
        df['Valor_Limpo'] = pd.to_numeric(df['Valor Total'].astype(str).str.replace(',', '.'), errors='coerce')
        invalid_val = df['Valor_Limpo'].isnull() | (df['Valor_Limpo'] <= 0)
        invalid_mask |= invalid_val
        quarantine_reasons.loc[invalid_val] += "Valor Total inválido ou zero; "

        # Normalização de Divergências
        df['Tem_Divergencia'] = df['Divergências'].notnull() & (df['Divergências'].astype(str).str.strip() != '')
        df['Divergencia_Classificada'] = df['Divergências'].fillna('Sem Divergência')

        # Separação: Válidos vs Quarentena
        valid_df = df[~invalid_mask].copy()
        quarantine_df = df[invalid_mask].copy()
        quarantine_df['Motivo_Quarentena'] = quarantine_reasons[invalid_mask]

        # Deduplicação na Base Válida
        if os.path.exists(self.storage_path):
            existing_df = pd.read_parquet(self.storage_path)
            new_records = valid_df[~valid_df['UUID_Registro'].isin(existing_df['UUID_Registro'])]
            duplicates_count = len(valid_df) - len(new_records)
            updated_dw = pd.concat([existing_df, new_records], ignore_index=True)
        else:
            new_records = valid_df
            duplicates_count = 0
            updated_dw = valid_df

        # Salva Data Warehouse
        updated_dw.to_parquet(self.storage_path, index=False)

        # Salva Quarentena (Append)
        if not quarantine_df.empty:
            if os.path.exists(self.quarantine_path):
                existing_q = pd.read_parquet(self.quarantine_path)
                quarantine_df = pd.concat([existing_q, quarantine_df], ignore_index=True)
            quarantine_df.to_parquet(self.quarantine_path, index=False)

        quality_score = (len(valid_df) / len(df)) * 100 if len(df) > 0 else 100.0

        return {
            "total_processado": len(df),
            "novos_inseridos": len(new_records),
            "duplicados_ignorados": duplicates_count,
            "enviados_quarentena": len(quarantine_df),
            "indice_qualidade": round(quality_score, 2),
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M")
        }