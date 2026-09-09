import math
import streamlit as st
from fpdf import FPDF

# Configuração visual da página
st.set_page_config(
    page_title="Gestor Elétrico NBR 5410",
    page_icon="⚡",
    layout="wide"
)

# Inicializa a lista de cômodos na sessão do navegador
if "comodos" not in st.session_state:
    st.session_state.comodos = []

# --- FUNÇÃO PARA GERAR O PDF PROFISSIONAL ---
def gerar_pdf(comodos, circuitos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Cabeçalho
    pdf.cell(190, 10, "LAUDO TÉCNICO DE DIMENSIONAMENTO ELÉTRICO", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 5, "Baseado estritamente nas diretrizes da Norma ABNT NBR 5410", ln=True, align="C")
    pdf.line(10, 27, 200, 27)
    pdf.ln(10)
    
    # 1. Resumo dos Ambientes
    pdf.set_font("Arial", "B", 13)
    pdf.cell(190, 8, "1. Relação de Ambientes Cadastrados", ln=True)
    pdf.set_font("Arial", "", 10)
    
    for c in comodos:
        tipo_str = "Úmida" if c['molhada'] else "Seca"
        texto_c = f"• {c['nome']} ({tipo_str}): {c['largura']:.2f}m x {c['comprimento']:.2f}m | Área: {c['area']:.2f}m² | Perímetro: {c['perimetro']:.2f}m"
        pdf.cell(190, 6, texto_c, ln=True)
    pdf.ln(5)
    
    # 2. Divisão e Dimensionamento dos Circuitos
    pdf.set_font("Arial", "B", 13)
    pdf.cell(190, 8, "2. Quadro de Distribuição de Circuitos (QGD)", ln=True)
    
    for circ in circuitos:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(190, 6, f"Circuito {circ['numero']} - {circ['nome']} ({circ['tensao']}V)", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(190, 5, f"  -> Potência Total: {circ['potencia']:.1f} VA | Corrente de Projeto (Ib): {circ['corrente']:.2f} A", ln=True)
        pdf.cell(190, 5, f"  -> Condutor: {circ['bitola']} mm² | Disjuntor Termomagnético: {circ['disjuntor']} A", ln=True)
        pdf.cell(190, 5, f"  -> Dispositivo DR: {circ['dr']} | DPS: Obrigatório Classe II no QGD", ln=True)
        pdf.ln(2)
        
    return pdf.output(dest="S")

# --- INTERFACE GRÁFICA (DASHBOARD) ---
st.title("⚡ Gestor de Projetos Elétricos Residencias")
st.caption("Cálculo de Cargas Mínimas, Dimensionamento e Divisão de Circuitos conforme NBR 5410")

# Layout em duas colunas: Esquerda (Entrada) | Direita (Resultados do Projeto)
col_cadastro, col_projeto = st.columns([1, 1.5], gap="large")

with col_cadastro:
    st.markdown("### 📝 Cadastrar Novo Cômodo")
    with st.form("form_comodo", clear_on_submit=True):
        nome_c = st.text_input("Nome do Cômodo", placeholder="Ex: Cozinha, Suíte 1, Lavanderia")
        tipo_c = st.radio("Tipo do Ambiente", ["Área Seca (Sala, Quarto, etc.)", "Área Úmida/Molhada (Cozinha, Banheiro, etc.)"])
        
        c1, c2 = st.columns(2)
        with c1:
            larg_c = st.number_input("Largura (m)", min_value=0.1, value=3.0, step=0.1)
        with c2:
            comp_c = st.number_input("Comprimento (m)", min_value=0.1, value=4.0, step=0.1)
            
        tensao_c = st.selectbox("Tensão Predominante (V)", [127, 220])
        tue_c = st.number_input("Adicionar TUE dedicada (W) - Opcional", min_value=0, value=0, step=100)
        
        botao_add = st.form_submit_button("➕ ADICIONAR AO PROJETO")
        
    if botao_add and nome_c:
        is_molhada = "Área Úmida" in tipo_c
        area_calc = larg_c * comp_c
        per_calc = 2 * (larg_c + comp_c)
        
        # Previsão de Cargas Mínimas (NBR 5410)
        va_ilum = 100 if area_calc < 6 else 100 + (math.floor((area_calc - 6) / 4) * 60)
        
        if not is_molhada:
            q_tugs = math.ceil(per_calc / 5)
            va_tugs = q_tugs * 100
        else:
            q_tugs = math.ceil(per_calc / 3.5)
            va_tugs = (3 * 600) + ((q_tugs - 3) * 100) if q_tugs > 3 else q_tugs * 600
            
        st.session_state.comodos.append({
            "nome": nome_c, "molhada": is_molhada, "largura": larg_c, "comprimento": comp_c,
            "area": area_calc, "perimetro": per_calc, "tensao": tensao_c,
            "va_ilum": va_ilum, "q_tugs": q_tugs, "va_tugs": va_tugs, "tue_w": tue_c
        })
        st.toast(f"✅ {nome_c} adicionado com sucesso!")

    if st.button("🗑️ Limpar Todo o Projeto"):
        st.session_state.comodos = []
        st.rerun()

# --- PROCESSAMENTO DO PROJETO E DIVISÃO DE CIRCUITOS ---
with col_projeto:
    st.markdown("### 📋 Painel do Projeto e Engenharia")
    
    if not st.session_state.comodos:
        st.info("Nenhum cômodo cadastrado ainda. Use o formulário ao lado para iniciar a lista da residência.")
    else:
        # AGREGADOR DE CIRCUITOS (Critérios NBR 5410 item 4.2.5)
        # Regras: 1. Iluminação separada de tomadas. 2. TUEs > 10A são circuitos exclusivos. 3. Separação por criticidade úmida.
        circuitos = []
        c_num = 1
        
        # Agrupamento 1: Iluminação Geral do Projeto
        total_va_ilum_127 = sum(c['va_ilum'] for c in st.session_state.comodos if c['tensao'] == 127)
        total_va_ilum_220 = sum(c['va_ilum'] for c in st.session_state.comodos if c['tensao'] == 220)
        
        if total_va_ilum_127 > 0:
            circuitos.append({"numero": c_num, "nome": "Iluminação Geral Residencial", "potencia": total_va_ilum_127, "tensao": 127, "tipo": "ILUM", "dr": "RECOMENDADO"})
            c_num += 1
        if total_va_ilum_220 > 0:
            circuitos.append({"numero": c_num, "nome": "Iluminação Geral Residencial", "potencia": total_va_ilum_220, "tensao": 220, "tipo": "ILUM", "dr": "RECOMENDADO"})
            c_num += 1
            
        # Agrupamento 2: Tomadas de Uso Geral (TUGs) - Separando Secas de Úmidas
        for c in st.session_state.comodos:
            if c['va_tugs'] > 0:
                nome_circ = f"TUGs - {c['nome']}"
                dr_necessario = "OBRIGATÓRIO (Área Úmida)" if c['molhada'] else "RECOMENDADO"
                circuitos.append({"numero": c_num, "nome": nome_circ, "potencia": c['va_tugs'], "tensao": c['tensao'], "tipo": "TUG", "dr": dr_necessario})
                c_num += 1
                
        # Agrupamento 3: Tomadas de Uso Específico (TUEs) - Circuitos Exclusivos obrigatórios
        for c in st.session_state.comodos:
            if c['tue_w'] > 0:
                circuitos.append({"numero": c_num, "nome": f"TUE Exclusiva - {c['nome']}", "potencia": c['tue_w'], "tensao": c['tensao'], "tipo": "TUE", "dr": "OBRIGATÓRIO"})
                c_num += 1

        # Dimensionamento individual de cada circuito gerado
        tabela_cabos = [(1.5, 17.5), (2.5, 24), (4.0, 32), (6.0, 41), (10.0, 57)]
        disjuntores_comerciais = [10, 16, 20, 25, 32, 40, 50]
        
        for circ in circuitos:
            circ['corrente'] = circ['potencia'] / circ['tensao']
            bitola_min = 1.5 if circ['tipo'] == "ILUM" else 2.5
            
            circ['bitola'], circ['disjuntor'] = 2.5, 20 # Padrão de segurança
            for bitola, capacidade in tabela_cabos:
                if bitola >= bitola_min and capacidade >= circ['corrente']:
                    circ['bitola'] = bitola
                    for dj in disjuntores_comerciais:
                        if dj >= circ['corrente'] and dj <= capacidade:
                            circ['disjuntor'] = dj
                            break
                    break

        # --- EXIBIÇÃO EM ABAS PROFISSIONAIS ---
        visualizacao, divisao_aba = st.tabs(["🏠 Dimensões por Cômodo", "🗂️ Quadro de Circuitos Dimensionados"])
        
        with visualizacao:
            for comodo in st.session_state.comodos:
                with st.expander(f"📍 {comodo['nome'].upper()} ({'Área Úmida' if comodo['molhada'] else 'Área Seca'})"):
                    m_a, m_p = st.columns(2)
                    m_a.metric("Área", f"{comodo['area']:.2f} m²")
                    m_p.metric("Perímetro", f"{comodo['perimetro']:.2f} m")
                    st.markdown(f"**Previsão NBR 5410:** Iluminação: `{comodo['va_ilum']} VA` | Tomadas TUGs: `{comodo['q_tugs']} un.` ({comodo['va_tugs']} VA)")
                    if comodo['tue_w'] > 0:
                        st.markdown(f"⚠️ **Carga Dedicada TUE:** `{comodo['tue_w']} W`")

        with divisao_aba:
            for circ in circuitos:
                cor_box = "red" if "OBRIGATÓRIO" in circ['dr'] else "blue"
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:15px; border-radius:8px; margin-bottom:12px; background-color:#1e222b;">
                    <h4 style="margin:0; color:#38bdf8;">Circuito {circ['numero']} - {circ['nome']}</h4>
                    <p style="margin:4px 0;"><b>Tensão:</b> {circ['tensao']}V | <b>Corrente de Projeto (Ib):</b> {circ['corrente']:.2f} A | <b>Carga Total:</b> {circ['potencia']:.0f} VA/W</p>
                    <p style="margin:4px 0; color:#4ade80;">🔹 <b>Condutor (Fio):</b> {circ['bitola']} mm² &nbsp;&nbsp;&nbsp;&nbsp; 🔹 <b>Disjuntor:</b> {circ['disjuntor']} A</p>
                    <p style="margin:4px 0; size:12px;">🛡️ <b>Dispositivo DR:</b> {circ['dr']} | <b>DPS:</b> Obrigatório Classe II</p>
                </div>
                """, unsafe_allow_html=True)
                
        # --- EXPORTAÇÃO DO LAUDO COMPLETO EM PDF ---
        st.markdown("---")
        st.markdown("#### 📂 Enviar Projeto para o Cliente")
        st.write("Clique no botão abaixo para gerar e fazer o download do documento técnico oficial em formato PDF. Substitui o printscreen tradicional por uma folha de entrega limpa.")
        
        dados_pdf = gerar_pdf(st.session_state.comodos, circuitos)
        st.download_button(
            label="📥 BAIXAR LAUDO TÉCNICO (PDF)",
            data=dados_pdf,
            file_name="laudo_dimensionamento_nbr5410.pdf",
            mime="application/pdf"
        )
