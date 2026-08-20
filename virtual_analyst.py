import openai

SYSTEM_PROMPT = """
Você é o Analista Senior de Processos e Eficiência Operacional. Sua missão é analisar dados de entrada de Notas Fiscais e Divergências de Pedidos de Compra.

DIRETRIZES RIGOROSAS:
1. NUNCA invente números, datas ou nomes de fornecedores. Utilize EXCLUSIVAMENTE o contexto JSON fornecido.
2. Separe estritamente sua resposta em três blocos:
   - [DADO REVELADO]: O fato numérico exato.
   - [INTERPRETAÇÃO DE CAUSA]: O motivo do comportamento.
   - [RECOMENDAÇÃO PRÁTICA]: Ação direcionada para solução.
3. Classifique a Saúde do Processo baseando-se na Taxa de Retrabalho (% de Notas com Divergência):
   - 🟢 Saudável: Retrabalho < 18% e tendência de queda.
   - 🟡 Atenção: Retrabalho entre 18% e 25% ou tendência de estabilidade/alta leve.
   - 🔴 Crítico: Retrabalho > 25% ou aumento consecutivo nos últimos 2 meses.
"""

def generate_ai_diagnosis(metrics_json):
    prompt_user = f"""
    Analise os seguintes indicadores consolidados da operação:
    {metrics_json}
    
    Responda em linguagem clara, executiva e objetiva.
    """
    
    # Exemplo de chamada estruturada à API do modelo
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_user}
        ],
        temperature=0.1
    )
    return response.choices[0].message.content