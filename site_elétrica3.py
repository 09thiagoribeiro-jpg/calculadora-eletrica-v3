import math
import streamlit as st
from fpdf import FPDF

st.set_page_config(page_title="Gestor Eletrico Pro", layout="wide")

# --- SISTEMA DE SEGURANÇA E SENHA ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("⚡ Gestor de Projetos Elétricos Avançado")
    st.markdown("### 🔒 Acesso Restrito")
    senha = st.text_input("Digite a senha para acessar o Gestor:", type="password")
    if st.button("Entrar"):
        if senha == "mudar123":  
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# --- INICIALIZAÇÃO DE VARIÁVEIS ---
if "comodos" not in st.session_state:
    st.session_state.comodos = []
if "tues_temporarias" not in st.session_state:
    st.session_state.tues_temporarias = []

def gerar_pdf(cliente, obra, responsavel, registro, comodos, circuitos):
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
    pdf.cell(190, 5, f"Responsavel Tecnico: {responsavel if responsavel else 'Nao informado'} | Registro: {registro if registro else 'Nao informado'}", ln=True)
    pdf.line(10, 47, 200, 47)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(190, 8, "1. Relacao de Ambientes Cadastrados", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for c in comodos:
        t_str = "Umida" if c['molhada'] else "Seca"
        txt = f"- {c['nome']} ({t_str}): Area {c['area']:.1f}m2 | Tensao Base: {c['tensao']}V | QGD: {c['distancia']:.1f}m"
        pdf.cell(190, 6, txt.encode('latin-1', 'ignore').decode('latin-1'), ln=True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(190, 8, "2. Quadro de Distribuicao de Circuitos Otimizado (QGD)", ln=True)
    for circ in circuitos:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(190, 6, f"Circuito {circ['numero']} - {circ['nome']} ({circ['tensao']}V)".encode('latin-1', 'ignore').decode('latin-1'), ln=True)
        pdf.set_font("Helvetica", "", 10)
        linha2 = f"  -> Potencia: {circ['potencia']:.0f} VA | Corrente: {circ['corrente']:.2f} A | Queda: {circ['queda_tensao']:.2f}%"
        pdf.cell(190, 5, linha2, ln=True)
        pdf.cell(190, 5, f"  -> Condutor: {circ['bitola']} mm2 | Disjuntor: {circ['disjuntor']} A", ln=True)
        pdf.cell(190, 5, f"  -> DR: {circ['dr']} | DPS: Obrigatorio Classe II", ln=True)
        pdf.ln(1)
    return pdf.output()

st.markdown("""
    <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); padding: 20px; border-radius: 12px; margin-bottom: 25px; text-align: center; color: white;">
        <h1 style="margin: 0; font-size: 32px;">⚡ RIBEIRO ELÉTRICA ⚡</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 14px;">Plataforma Homologada NBR 5410 - Gestão & Dimensionamento Avançado</p>
    </div>
""", unsafe_allow_html=True)
st.markdown("### 👤 Identificação Profissional e do Cliente")
c_cli1, c_cli2 = st.columns(2)
nome_cliente = c_cli1.text_input("Nome do Cliente", placeholder="Ex: Joao Silva")
endereco_obra = c_cli2.text_input("Endereço da Obra", placeholder="Ex: Rua das Palmeiras, 150")

c_prof1, c_prof2 = st.columns(2)
nome_responsavel = c_prof1.text_input("Responsável Técnico", placeholder="Ex: Eng. Pedro Santos")
registro_tecnico = c_prof2.text_input("Registro Profissional (CREA / CFT)", placeholder="Ex: 506.XXX.XXX-SP")

st.markdown("---")
col_cadastro, col_projeto = st.columns([1.1, 1.4], gap="large")

with col_cadastro:
    st.markdown("### 📝 Cadastrar Novo Cômodo")
    nome_c = st.text_input("Nome do Cômodo", placeholder="Ex: Suite Master, Cozinha")
    tipo_c = st.radio("Classificação do Ambiente", ["Área Seca (Quartos, Sala, Corredores)", "Área Úmida/Molhada (Cozinha, Banheiro, Area Serv.)"])
    
    c1, c2, c3 = st.columns(3)
    larg_c = c1.number_input("Largura (m)", min_value=0.1, value=3.0, step=0.1)
    comp_c = c2.number_input("Comprimento (m)", min_value=0.1, value=4.0, step=0.1)
    dist_c = c3.number_input("Distância ao QGD (m)", min_value=1.0, value=10.0, step=1.0)
        
    tensao_c = st.selectbox("Tensão da Iluminação e Tomadas Gerais (TUGs)", (127, 220))
    
    st.markdown("#### 🔌 Cargas Especiais / TUEs do Cômodo")
    col_tue_nome, col_tue_w, col_tue_v = st.columns([1.2, 0.9, 0.7])
    nome_tue = col_tue_nome.text_input("Equipamento", placeholder="Ex: Ar Condicionado")
    w_tue = col_tue_w.number_input("Potência (W)", min_value=0, value=0, step=100)
    v_tue = col_tue_v.selectbox("Tensão (V)", (220, 127), key="tensao_tue_select")
        
    if st.button("➕ Vincular TUE"):
        if nome_tue and w_tue > 0:
            st.session_state.tues_temporarias.append({"equipamento": nome_tue, "potencia": w_tue, "tensao": v_tue})
            st.toast(f"TUE '{nome_tue}' vinculada.")
            
    # Gerenciador de Remoção de TUEs individuais
    if st.session_state.tues_temporarias:
        st.write("**TUEs vinculadas provisoriamente:**")
        tues_para_remover = []
        for idx, t in enumerate(st.session_state.tues_temporarias):
            t_col1, t_col2 = st.columns([4, 1])
            t_col1.caption(f"• {t['equipamento']}: {t['potencia']}W ({t['tensao']}V)")
            if t_col2.button("❌", key=f"del_tue_temp_{idx}"):
                tues_para_remover.append(idx)
        
        if tues_para_remover:
            for index in sorted(tues_para_remover, reverse=True):
                st.session_state.tues_temporarias.pop(index)
            st.rerun()
            
    st.markdown("---")
    if st.button("💾 SALVAR CÔMODO NO PROJETO", type="primary"):
        if nome_c:
            is_molhada = "Úmida" in tipo_c
            area_calc = larg_c * comp_c
            per_calc = 2 * (larg_c + comp_c)
            va_ilum = 100 if area_calc < 6 else 100 + (math.floor((area_calc - 6) / 4) * 60)
            
            q_tugs = math.ceil(per_calc / 3.5) if is_molhada else math.ceil(per_calc / 5)
            va_tugs = ((3 * 600) + ((q_tugs - 3) * 100) if q_tugs > 3 else q_tugs * 600) if is_molhada else q_tugs * 100
                
            st.session_state.comodos.append({
                "nome": nome_c, "molhada": is_molhada, "largura": larg_c, "comprimento": comp_c,
                "area": area_calc, "perimetro": per_calc, "tensao": tensao_c, "distancia": dist_c,
                "va_ilum": va_ilum, "q_tugs": q_tugs, "va_tugs": va_tugs, "tues": list(st.session_state.tues_temporarias)
            })
            st.session_state.tues_temporarias = []
            st.rerun()

    if st.button("🗑️ Limpar Todo o Projeto"):
        st.session_state.comodos = []
        st.session_state.tues_temporarias = []
        st.rerun()
with col_projeto:
    st.markdown("### 📋 Quadro de Distribuição & Edição")
    if not st.session_state.comodos:
        st.info("Nenhum cômodo cadastrado.")
    else:
        circuitos = []
        c_num = 1
        
        for v in (127, 220):
            ilum_comodos = [c for c in st.session_state.comodos if c['tensao'] == v]
            if ilum_comodos:
                circuitos.append({
                    "numero": c_num, "nome": f"Iluminacao Geral ({v}V)", 
                    "potencia": sum(c['va_ilum'] for c in ilum_comodos),
                    "tensao": v, "tipo": "ILUM", "dr": "RECOMENDADO", "distancia": max(c['distancia'] for c in ilum_comodos)
                })
                c_num += 1
        
        for v in (127, 220):
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
                    "potencia": t['potencia'], "tensao": t['tensao'], "tipo": "TUE", "dr": "OBRIGATORIO", "distancia": c['distancia']
                })
                c_num += 1

        resumo_disjuntores = {}
        resumo_cabos = {1.5: 0.0, 2.5: 0.0, 4.0: 0.0, 6.0: 0.0, 10.0: 0.0}

        for circ in circuitos:
            circ['corrente'] = circ['potencia'] / circ['tensao']
            b_final = 1.5 if circ['tipo'] == "ILUM" else 2.5
            
            while True:
                cap = 17.5 if b_final==1.5 else 24.0 if b_final==2.5 else 32.0 if b_final==4.0 else 41.0 if b_final==6.0 else 57.0
                q_v = (2.0 * 0.0178 * circ['distancia'] * circ['corrente']) / b_final
                pct = (q_v / circ['tensao']) * 100.0
                
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

            i_proj = circ['corrente']
            dj_adequado = 10 if i_proj <= 10 else 16 if i_proj <= 16 else 20 if i_proj <= 20 else 25 if i_proj <= 25 else 32 if i_proj <= 32 else 40
            circ['disjuntor'] = dj_adequado
            
            resumo_disjuntores[dj_adequado] = resumo_disjuntores.get(dj_adequado, 0) + 1
            resumo_cabos[circ['bitola']] += circ['distancia'] * 3.0

        v_aba, d_aba, mat_aba = st.tabs(["🏠 Gerenciar Comodos", "🗂️ QGD (Circuitos)", "📦 Materiais"])
        
        with v_aba:
            comodo_remover = None
            for idx, co in enumerate(st.session_state.comodos):
                with st.expander(f"📍 {co['nome'].upper()}"):
                    st.write(f"Area: {co['area']:.1f} m2 | Distancia: {co['distancia']}m")
                    
                    # Gerenciador de TUEs dentro do cômodo já salvo
                    if co['tues']:
                        st.write("Cargas Especiais (TUEs):")
                        tues_internas_para_remover = []
                        for t_idx, t in enumerate(co['tues']):
                            t_col1, t_col2 = st.columns([5, 1])
                            t_col1.write(f"🔸 {t['equipamento']} ({t['potencia']}W em {t['tensao']}V)")
                            if t_col2.button("🗑️", key=f"del_tue_salva_{idx}_{t_idx}"):
                                tues_internas_para_remover.append(t_idx)
                        
                        if tues_internas_para_remover:
                            for t_index in tues_internas_para_remover:
                                co['tues'].pop(t_index)
                            st.rerun()
                    
                    # Botão para excluir o cômodo inteiro
                    if st.button("Remover Comodo Completo", key=f"del_comodo_{idx}"):
                        comodo_remover = idx
            
            if comodo_remover is not None:
                st.session_state.comodos.pop(comodo_remover)
                st.rerun()

        with d_aba:
            for circ in circuitos:
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:12px; border-radius:6px; margin-bottom:10px; background-color:#1e222b;">
                    <h5 style="margin:0; color:#38bdf8;">Circuito {circ['numero']} - {circ['nome']}</h5>
                    <p style="margin:2px 0; font-size:13px;"><b>Tensao:</b> {circ['tensao']}V | <b>Carga:</b> {circ['potencia']:.0f} VA | <b>Queda:</b> {circ['queda_tensao']:.2f}%</p>
                    <p style="margin:2px 0; color:#4ade80; font-size:13px;">🔹 <b>Fio:</b> {circ['bitola']} mm² &nbsp;&nbsp;&nbsp;&nbsp; 🔹 <b>Disjuntor:</b> {circ['disjuntor']} A</p>
                </div>
                """, unsafe_allow_html=True)
                
        with mat_aba:
            st.markdown("#### 🛒 Estimativa Quantitativa")
            for amp, quant in resumo_disjuntores.items():
                st.write(f"• Disjuntor {amp}A: **{quant} un.**")
            for bit, metros in resumo_cabos.items():
                if metros > 0:
                    st.write(f"• Cabo {bit} mm²: **{metros:.1f} metros**")

        st.markdown("---")
        dados_pdf = gerar_pdf(nome_cliente, endereco_obra, nome_responsavel, registro_tecnico, st.session_state.comodos, circuitos)
        st.download_button(label="📥 DOWNLOAD LAUDO EM PDF", data=bytes(dados_pdf), file_name="laudo_eletrico.pdf", mime="application/pdf")
