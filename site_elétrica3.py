import math
import streamlit as st
from fpdf import FPDF

st.set_page_config(page_title="Gestor NBR 5410", layout="wide")

if "comodos" not in st.session_state:
    st.session_state.comodos = []
if "tues_temporarias" not in st.session_state:
    st.session_state.tues_temporarias = []

def gerar_pdf(cliente, obra, comodos, circuitos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "LAUDO TECNICO DE DIMENSIONAMENTO ELETRICO", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(190, 5, "Baseado estritamente nas diretrizes da Norma ABNT NBR 5410", ln=True, align="C")
    pdf.line(10, 27, 200, 27)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(190, 6, f"CLIENTE: {cliente.upper() if cliente else 'NAO INFORMADO'}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(190, 5, f"Endereco da Obra: {obra if obra else 'Nao informado'}", ln=True)
    pdf.line(10, 42, 200, 42)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(190, 8, "1. Relacao de Ambientes Cadastrados", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for c in comodos:
        t_str = "Umida" if c['molhada'] else "Seca"
        txt = f"- {c['nome']} ({t_str}): {c['largura']:.1f}mx{c['comprimento']:.1f}m | Distancia ao QGD: {c['distancia']:.1f}m"
        pdf.cell(190, 6, txt.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(190, 8, "2. Quadro de Distribuicao de Circuitos Otimizado (QGD)", ln=True)
    for circ in circuitos:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(190, 6, f"Circuito {circ['numero']} - {circ['nome']} ({circ['tensao']}V)".encode('latin-1', 'ignore').decode('latin-1'), ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(190, 5, f"  -> Potencia: {circ['potencia']:.0f} VA | Corrente: {circ['corrente']:.2f} A | Queda: {circ['queda']:.2f}%", ln=True)
        pdf.cell(190, 5, f"  -> Condutor: {circ['bitola']} mm2 | Disjuntor: {circ['disjuntor']} A", ln=True)
        pdf.cell(190, 5, f"  -> DR: {circ['dr']} | DPS: Obrigatorio Classe II", ln=True)
        pdf.ln(1)
    return pdf.output()

st.title("⚡ Gestor de Projetos Elétricos Avançado")
st.caption("Otimização de Circuitos, Cálculo de Queda de Tensão e Laudos Técnicos NBR 5410")
st.markdown("### 👤 Identificação do Projeto")
c_cli1, c_cli2 = st.columns(2)
nome_cliente = c_cli1.text_input("Nome do Cliente", placeholder="Ex: Joao Silva")
endereco_obra = c_cli2.text_input("Endereço da Obra", placeholder="Ex: Rua das Palmeiras, 150")

st.markdown("---")
col_cadastro, col_projeto = st.columns([1.1, 1.4], gap="large")

with col_cadastro:
    st.markdown("### 📝 Cadastrar Novo Cômodo")
    nome_c = st.text_input("Nome do Cômodo", placeholder="Ex: Quarto 1, Cozinha")
    tipo_c = st.radio("Tipo do Ambiente", ["Área Seca", "Área Úmida/Molhada"])
    
    c1, c2, c3 = st.columns(3)
    larg_c = c1.number_input("Largura (m)", min_value=0.1, value=3.0, step=0.1)
    comp_c = c2.number_input("Comprimento (m)", min_value=0.1, value=4.0, step=0.1)
    dist_c = c3.number_input("Distância ao QGD (m)", min_value=1.0, value=10.0, step=1.0)
        
    tensao_c = st.selectbox("Tensão Predominante (V)", [127, 220])
    
    st.markdown("#### 🔌 Adicionar TUEs deste Cômodo")
    col_tue_nome, col_tue_w = st.columns([1.2, 1.0])
    nome_tue = col_tue_nome.text_input("Nome do Equipamento", placeholder="Ex: Chuveiro, Ar Cond.")
    w_tue = col_tue_w.number_input("Potência (W)", min_value=0, value=0, step=100)
        
    if st.button("➕ Vincular TUE"):
        if nome_tue and w_tue > 0:
            st.session_state.tues_temporarias.append({"equipamento": nome_tue, "potencia": w_tue})
            st.toast(f"TUE '{nome_tue}' vinculada.")
            
    if st.session_state.tues_temporarias:
        for t in st.session_state.tues_temporarias:
            st.caption(f"• {t['equipamento']}: {t['potencia']} W")
            
    st.markdown("---")
    if st.button("💾 SALVAR CÔMODO NO PROJETO", type="primary"):
        if nome_c:
            is_molhada = "Úmida" in tipo_c
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
                "area": area_calc, "perimetro": per_calc, "tensao": tensao_c, "distancia": dist_c,
                "va_ilum": va_ilum, "q_tugs": q_tugs, "va_tugs": va_tugs, "tues": list(st.session_state.tues_temporarias)
            })
            st.session_state.tues_temporarias = []
            st.rerun()

    if st.button("🗑️ Limpar Projeto"):
        st.session_state.comodos = []
        st.session_state.tues_temporarias = []
        st.rerun()

with col_projeto:
    st.markdown("### 📋 Quadro de Distribuição Otimizado (QGD)")
    if not st.session_state.comodos:
        st.info("Nenhum cômodo cadastrado.")
    else:
        circuitos = []
        c_num = 1
        
        for v in:
            ilum_comodos = [c for c in st.session_state.comodos if c['tensao'] == v]
            if ilum_comodos:
                circuitos.append({
                    "numero": c_num, "nome": f"Iluminacao Geral ({v}V)", 
                    "potencia": sum(c['va_ilum'] for c in ilum_comodos),
                    "tensao": v, "tipo": "ILUM", "dr": "RECOMENDADO", "distancia": max(c['distancia'] for c in ilum_comodos)
                })
                c_num += 1
        
        for v in:
            umidas = [c for c in st.session_state.comodos if c['tensao'] == v and c['molhada']]
            for u in umidas:
                circuitos.append({
                    "numero": c_num, "nome": f"TUGs Cozinha/Servico - {u['nome']}", "potencia": u['va_tugs'],
                    "tensao": v, "tipo": "TUG", "dr": "OBRIGATORIO", "distancia": u['distancia']
                })
                c_num += 1
            
            secas = [c for c in st.session_state.comodos if c['tensao'] == v and not c['molhada']]
            c_nome, c_va, c_dist = [], 0, 0
            limite = 1200 if v == 127 else 2500
            
            for s in secas:
                if c_va + s['va_tugs'] <= limite:
                    c_nome.append(s['nome'])
                    c_va += s['va_tugs']
                    c_dist = max(c_dist, s['distancia'])
                else:
                    if c_va > 0:
                        circuitos.append({"numero": c_num, "nome": f"TUGs Secas Agrupadas ({', '.join(c_nome)})", "potencia": c_va, "tensao": v, "tipo": "TUG", "dr": "RECOMENDADO", "distancia": c_dist})
                        c_num += 1
                    c_nome, c_va, c_dist = [s['nome']], s['va_tugs'], s['distancia']
            if c_va > 0:
                circuitos.append({"numero": c_num, "nome": f"TUGs Secas Agrupadas ({', '.join(c_nome)})", "potencia": c_va, "tensao": v, "tipo": "TUG", "dr": "RECOMENDADO", "distancia": c_dist})
                c_num += 1

        for c in st.session_state.comodos:
            for t in c['tues']:
                circuitos.append({
                    "numero": c_num, "nome": f"TUE Exclusiva - {t['equipamento']} ({c['nome']})",
                    "potencia": t['potencia'], "tensao": c['tensao'], "tipo": "TUE", "dr": "OBRIGATORIO", "distancia": c['distancia']
                })
                c_num += 1

        for circ in circuitos:
            circ['corrente'] = circ['potencia'] / circ['tensao']
            b_final = 1.5 if circ['tipo'] == "ILUM" else 2.5
            
            while True:
                cap = 17.5 if b_final==1.5 else 24 if b_final==2.5 else 32 if b_final==4.0 else 41 if b_final==6.0 else 57
                q_v = (2 * 0.0178 * circ['distancia'] * circ['corrente']) / b_final
                pct = (q_v / circ['tensao']) * 100
                
                if circ['corrente'] <= cap and pct <= 4.0:
                    circ['bitola'] = b_final
                    circ['queda_tensao'] = pct
                    break
                else:
                    b_final = 2.5 if b_final==1.5 else 4.0 if b_final==2.5 else 6.0 if b_final==4.0 else 10.0
                    if b_final == 10.0:
                        circ['bitola'] = 10.0
                        circ['queda_tensao'] = pct
                        break

            # Lista comercial corrigida
            disjuntores_comerciais = [10, 16, 20, 25, 32, 40]
            circ['disjuntor'] = 40
            for dj in disjuntores_comerciais:
                if dj >= circ['corrente']:
                    circ['disjuntor'] = dj
                    break

        v_aba, d_aba = st.tabs(["🏠 Cômodos", "🗂️ Circuitos (QGD)"])
        with v_aba:
            for co in st.session_state.comodos:
                with st.expander(f"📍 {co['nome'].upper()}"):
                    st.write(f"Área: {co['area']:.1f} m2 | Distância ao Quadro: {co['distancia']:.1f}m")
                    if co['tues']:
                        for t in co['tues']:
                            st.caption(f"🔸 TUE: {t['equipamento']} ({t['potencia']}W)")

        with d_aba:
            for circ in circuitos:
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:12px; border-radius:6px; margin-bottom:10px; background-color:#1e222b;">
                    <h5 style="margin:0; color:#38bdf8;">Circuito {circ['numero']} - {circ['nome']}</h5>
                    <p style="margin:2px 0; font-size:13px;"><b>Tensão:</b> {circ['tensao']}V | <b>Carga:</b> {circ['potencia']:.0f} VA | <b>Queda:</b> {circ['queda_tensao']:.2f}%</p>
                    <p style="margin:2px 0; color:#4ade80; font-size:13px;">🔹 <b>Fio:</b> {circ['bitola']} mm² &nbsp;&nbsp;&nbsp;&nbsp; 🔹 <b>Disjuntor:</b> {circ['disjuntor']} A</p>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("---")
        dados_pdf = gerar_pdf(nome_cliente, endereco_obra, st.session_state.comodos, circuitos)
        st.download_button(label="📥 DOWNLOAD LAUDO EM PDF", data=bytes(dados_pdf), file_name="laudo_eletrico.pdf", mime="application/pdf")

