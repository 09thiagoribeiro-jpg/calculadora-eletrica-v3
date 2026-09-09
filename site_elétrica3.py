import math
import streamlit as st
from fpdf import FPDF

# Configuração visual da página
st.set_page_config(
    page_title="Gestor Elétrico NBR 5410",
    page_icon="⚡",
    layout="wide"
)

# Inicializa as listas na sessão do navegador
if "comodos" not in st.session_state:
    st.session_state.comodos = []
if "tues_temporarias" not in st.session_state:
    st.session_state.tues_temporarias = []

# --- FUNÇÃO PARA GERAR O PDF (LATIN-1 COMPATÍVEL) ---
def gerar_pdf(comodos, circuitos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    
    # Cabeçalho
    pdf.cell(190, 10, "LAUDO TECNICO DE DIMENSIONAMENTO ELETRICO", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(190, 5, "Baseado estritamente nas diretrizes da Norma ABNT NBR 5410", ln=True, align="C")
    pdf.line(10, 27, 200, 27)
    pdf.ln(10)
    
    # 1. Resumo dos Ambientes
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(190, 8, "1. Relacao de Ambientes Cadastrados", ln=True)
    pdf.set_font("Helvetica", "", 10)
    
    for c in comodos:
        tipo_str = "Umida" if c['molhada'] else "Seca"
        texto_c = f"- {c['nome']} ({tipo_str}): {c['largura']:.2f}m x {c['comprimento']:.2f}m | Area: {c['area']:.2f}m2 | Perimetro: {c['perimetro']:.2f}m"
        texto_limpo = texto_c.encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(190, 6, texto_limpo, ln=True)
    pdf.ln(5)
    
    # 2. Divisão e Dimensionamento dos Circuitos
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(190, 8, "2. Quadro de Distribuicao de Circuitos (QGD)", ln=True)
    
    for circ in circuitos:
        pdf.set_font("Helvetica", "B", 10)
        linha1 = f"Circuito {circ['numero']} - {circ['nome']} ({circ['tensao']}V)"
        pdf.cell(190, 6, linha1.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
        
        pdf.set_font("Helvetica", "", 10)
        linha2 = f"  -> Potencia Total: {circ['potencia']:.1f} VA | Corrente de Projeto (Ib): {circ['corrente']:.2f} A"
        pdf.cell(190, 5, linha2.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
        
        linha3 = f"  -> Condutor: {circ['bitola']} mm2 | Disjuntor Termomagnetico: {circ['disjuntor']} A"
        pdf.cell(190, 5, linha3.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
        
        linha4 = f"  -> Dispositivo DR: {circ['dr']} | DPS: Obrigatorio Classe II no QGD"
        pdf.cell(190, 5, linha4.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
        pdf.ln(2)
        
    return pdf.output()

# --- INTERFACE GRÁFICA (DASHBOARD) ---
st.title("⚡ Gestor de Projetos Elétricos Residenciais")
st.caption("Cálculo de Cargas Mínimas, Dimensionamento e Divisão de Circuitos conforme NBR 5410")
# Layout em duas colunas: Esquerda (Entrada) | Direita (Resultados do Projeto)
col_cadastro, col_projeto = st.columns([1.1, 1.4], gap="large")

with col_cadastro:
    st.markdown("### 📝 Cadastrar Novo Cômodo")
    nome_c = st.text_input("Nome do Cômodo", placeholder="Ex: Suite Master, Cozinha, Banheiro")
    tipo_c = st.radio("Tipo do Ambiente", ["Área Seca (Sala, Quarto, etc.)", "Área Úmida/Molhada (Cozinha, Banheiro, etc.)"])
    
    c1, c2 = st.columns(2)
    with c1:
        larg_c = st.number_input("Largura (m)", min_value=0.1, value=3.0, step=0.1)
    with c2:
        comp_c = st.number_input("Comprimento (m)", min_value=0.1, value=4.0, step=0.1)
        
    tensao_c = st.selectbox("Tensão Predominante do Cômodo (V)", [127, 220])
    
    # --- SUB-FORMULÁRIO DE TUES INDIVIDUAIS ---
    st.markdown("#### 🔌 Cargas Especiais / TUEs deste Cômodo")
    col_tue_nome, col_tue_w = st.columns([1.2, 1.0])
    with col_tue_nome:
        nome_tue = st.text_input("Nome do Equipamento", placeholder="Ex: Chuveiro, Ar Cond.", key="input_nome_tue")
    with col_tue_w:
        w_tue = st.number_input("Potência (W)", min_value=0, value=0, step=100, key="input_w_tue")
        
    if st.button("➕ Vincular TUE a este Cômodo"):
        if nome_tue and w_tue > 0:
            st.session_state.tues_temporarias.append({"equipamento": nome_tue, "potencia": w_tue})
            st.toast(f"TUE '{nome_tue}' vinculada provisoriamente.")
            
    if st.session_state.tues_temporarias:
        st.write("**TUEs vinculadas para este ambiente:**")
        for idx, t in enumerate(st.session_state.tues_temporarias):
            st.caption(f"• {t['equipamento']}: {t['potencia']} W")
            
    st.markdown("---")
    
    if st.button("💾 SALVAR CÔMODO NO PROJETO", type="primary"):
        if nome_c:
            is_molhada = "Área Úmida" in tipo_c
            area_calc = larg_c * comp_c
            per_calc = 2 * (larg_c + comp_c)
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
                "va_ilum": va_ilum, "q_tugs": q_tugs, "va_tugs": va_tugs, 
                "tues": list(st.session_state.tues_temporarias)
            })
            st.session_state.tues_temporarias = []
            st.rerun()
        else:
            st.error("Insira o nome do cômodo antes de salvar.")

    if st.button("🗑️ Limpar Todo o Projeto"):
        st.session_state.comodos = []
        st.session_state.tues_temporarias = []
        st.rerun()

# --- PROCESSAMENTO DO PROJETO E DIVISÃO DE CIRCUITOS ---
with col_projeto:
    st.markdown("### 📋 Painel do Projeto e Engenharia")
    
    if not st.session_state.comodos:
        st.info("Nenhum cômodo cadastrado ainda. Use o formulário ao lado para iniciar.")
    else:
        circuitos = []
        c_num = 1
        
        total_va_ilum_127 = sum(c['va_ilum'] for c in st.session_state.comodos if c['tensao'] == 127)
        total_va_ilum_220 = sum(c['va_ilum'] for c in st.session_state.comodos if c['tensao'] == 220)
        
        if total_va_ilum_127 > 0:
            circuitos.append({"numero": c_num, "nome": "Iluminacao Geral Residencial", "potencia": total_va_ilum_127, "tensao": 127, "tipo": "ILUM", "dr": "RECOMENDADO"})
            c_num += 1
        if total_va_ilum_220 > 0:
            circuitos.append({"numero": c_num, "nome": "Iluminacao Geral Residencial", "potencia": total_va_ilum_220, "tensao": 220, "tipo": "ILUM", "dr": "RECOMENDADO"})
            c_num += 1
            
        for c in st.session_state.comodos:
            if c['va_tugs'] > 0:
                nome_circ = f"TUGs - {c['nome']}"
                dr_necessario = "OBRIGATORIO (Area Umida)" if c['molhada'] else "RECOMENDADO"
                circuitos.append({"numero": c_num, "nome": nome_circ, "potencia": c['va_tugs'], "tensao": c['tensao'], "tipo": "TUG", "dr": dr_necessario})
                c_num += 1
                
        for c in st.session_state.comodos:
            for t in c['tues']:
                nome_exclusivo = f"TUE Exclusiva - {t['equipamento']} ({c['nome']})"
                circuitos.append({"numero": c_num, "nome": nome_exclusivo, "potencia": t['potencia'], "tensao": c['tensao'], "tipo": "TUE", "dr": "OBRIGATORIO"})
                c_num += 1

        # Tabelas de dimensionamento sem formatações conflitantes
        tabela_cabos = [(1.5, 17.5), (2.5, 24.0), (4.0, 32.0), (6.0, 41.0), (10.0, 57.0)]
        disjuntores_comerciais = [10, 16, 20, 25, 32, 40, 50, 63]
        
        for circ in circuitos:
            circ['corrente'] = circ['potencia'] / circ['tensao']
            bitola_min = 1.5 if circ['tipo'] == "ILUM" else 2.5
            circ['bitola'], circ['disjuntor'] = 2.5, 20
            
            for bitola, capacidade in tabela_cabos:
                if bitola >= bitola_min and circ['corrente'] <= capacidade:
                    circ['bitola'] = bitola
                    for dj in disjuntores_comerciais:
                        if dj >= circ['corrente'] and dj <= capacidade:
                            circ['disjuntor'] = dj
                            break
                    break

        visualizacao, divisao_aba = st.tabs(["🏠 Dimensões por Cômodo", "🗂️ Quadro de Circuitos Dimensionados (QGD)"])
        
        with visualizacao:
            for comodo in st.session_state.comodos:
                with st.expander(f"📍 {comodo['nome'].upper()}"):
                    st.write(f"Área: {comodo['area']:.2f} m² | Perímetro: {comodo['perimetro']:.2f} m")
                    st.write(f"Iluminação: {comodo['va_ilum']} VA | Tomadas Gerais: {comodo['va_tugs']} VA")
                    if comodo['tues']:
                        for t in comodo['tues']:
                            st.write(f"🔸 {t['equipamento']}: {t['potencia']} W (Circuito Individual)")

        with divisao_aba:
            for circ in circuitos:
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:15px; border-radius:8px; margin-bottom:12px; background-color:#1e222b;">
                    <h4 style="margin:0; color:#38bdf8;">Circuito {circ['numero']} - {circ['nome']}</h4>
                    <p style="margin:4px 0;"><b>Tensão:</b> {circ['tensao']}V | <b>Corrente (Ib):</b> {circ['corrente']:.2f} A | <b>Carga:</b> {circ['potencia']:.0f} VA</p>
                    <p style="margin:4px 0; color:#4ade80;">🔹 <b>Condutor:</b> {circ['bitola']} mm² &nbsp;&nbsp;&nbsp;&nbsp; 🔹 <b>Disjuntor:</b> {circ['disjuntor']} A</p>
                    <p style="margin:4px 0;">🛡️ <b>DR:</b> {circ['dr']} | <b>DPS:</b> Obrigatório Classe II</p>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("---")
        dados_pdf = gerar_pdf(st.session_state.comodos, circuitos)
        st.download_button(
            label="📥 BAIXAR LAUDO TÉCNICO COMPLETO (PDF)",
            data=bytes(dados_pdf),
            file_name="laudo_dimensionamento_nbr5410.pdf",
            mime="application/pdf"
        )

