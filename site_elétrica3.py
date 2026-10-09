import math
import json
import streamlit as st
from fpdf import FPDF
from docx import Document
from io import BytesIO

st.set_page_config(page_title="Gestor Eletrico Pro NBR 5410", layout="wide")

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

# --- INICIALIZAÇÃO DE VARIÁVEIS DE SESSÃO ---
if "comodos" not in st.session_state:
    st.session_state.comodos = []
if "tues_temporarias" not in st.session_state:
    st.session_state.tues_temporarias = []
if "comodos_contagem" not in st.session_state:
    st.session_state.comodos_contagem = {}

# --- GESTÃO DE BACKUP E PERSISTÊNCIA EM JSON ---
st.sidebar.markdown("### 💾 Backup do Projeto")
json_string = json.dumps(st.session_state.comodos, indent=4)
st.sidebar.download_button(
    label="📤 Exportar Projeto (.JSON)",
    data=json_string,
    file_name="projeto_eletrico.json",
    mime="application/json"
)

arquivo_importado = st.sidebar.file_uploader("📥 Importar Projeto (.JSON)", type=["json"])
if arquivo_importado is not None:
    try:
        dados_carregados = json.load(arquivo_importado)
        st.session_state.comodos = dados_carregados
        contagem = {}
        for c in dados_carregados:
            if 'nome' in c:
                partes_nome = c['nome'].rsplit(' ', 1)
                nome_puro = partes_nome[0]
                contagem[nome_puro] = contagem.get(nome_puro, 0) + 1
        st.session_state.comodos_contagem = contagem
        st.sidebar.success("Projeto carregado com sucesso!")
    except Exception as e:
        st.sidebar.error("Erro ao ler o arquivo JSON.")
def gerar_pdf(cliente, obra, responsavel, registro, concessionaria, circuitos, padrao, inc_padrao):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(190, 10, "LAUDO TECNICO DE DIMENSIONAMENTO ELETRICO RESIDENCIAL", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(190, 5, "Em estrita conformidade com a ABNT NBR 5410 e Normas de Distribuicao Local", ln=True, align="C")
    pdf.line(10, 27, 200, 27)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(190, 6, f"CLIENTE: {cliente.upper() if cliente else 'NAO INFORMADO'}", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(190, 5, f"Endereco da Obra: {obra if obra else 'Nao informado'}", ln=True)
    pdf.cell(190, 5, f"Responsavel Tecnico: {responsavel if responsavel else 'Nao informado'} | Registro: {registro if registro else 'Nao informado'}", ln=True)
    pdf.cell(190, 5, f"Regiao Regulamentadora / Concessionaria: {concessionaria}", ln=True)
    pdf.line(10, 52, 200, 52)
    pdf.ln(5)
    
    if inc_padrao:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(190, 8, f"PADRAO DE ENTRADA RECOMENDADO ({concessionaria}):", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(190, 5, f"Tipo de Atendimento: {padrao['tipo']} | Demanda Calculada: {padrao['demanda_kva']:.2f} kVA", ln=True)
        pdf.cell(190, 5, f"Disjuntor Termomagnetico Geral: {padrao['disjuntor']} A | Condutor de Entrada: {padrao['cabo']} mm2", ln=True)
        pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(190, 8, "1. Memoria de Calculo dos Circuitos Terminais (QGD)", ln=True)
    for circ in circuitos:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(190, 6, f"Circuito {circ['numero']} - {circ['nome']} ({circ['tensao']}V)", ln=True)
        pdf.set_font("Helvetica", "", 9)
        linha2 = f"  -> Potencia: {circ['potencia']:.0f} VA | Corrente Ib: {circ['corrente']:.2f} A | Fator Corrigido Iz: {circ['iz_corrigida']:.2f} A"
        pdf.cell(190, 5, linha2, ln=True)
        pdf.cell(190, 5, f"  -> Condutor: {circ['bitola']} mm2 | Disjuntor DIN: {circ['disjuntor']} A | Queda de Tensao: {circ['queda_tensao']:.2f}% ({circ['dr']})", ln=True)
        pdf.ln(1)
    
    # CORREÇÃO DEFINITIVA DO ERRO: Retorna os bytes do PDF gerados pela biblioteca fpdf2 atualizada
    return pdf.output()

def gerar_word(cliente, obra, responsavel, registro, concessionaria, circuitos, padrao, inc_padrao):
    doc = Document()
    doc.add_heading("MEMORIAL DESCRITIVO E MEMÓRIA DE CÁLCULO ELÉTRICO", level=1)
    p = doc.add_paragraph()
    p.add_run(f"Cliente: {cliente}\nEndereço: {obra}\nConcessionária Alvo: {concessionaria}\n").bold = True
    p.add_run(f"Responsável Técnico: {responsavel} | Registro: {registro}\n")
    
    if inc_padrao:
        doc.add_heading("1. Dimensionamento do Padrão de Entrada Geral (Concessionária)", level=2)
        doc.add_paragraph(f"Tipo de Fornecimento Secundário: {padrao['tipo']}\n"
                          f"Demanda Máxima Diversificada: {padrao['demanda_kva']:.2f} kVA\n"
                          f"Proteção Geral (Disjuntor Caixa): {padrao['disjuntor']} A\n"
                          f"Seção Reta do Condutor de Entrada: {padrao['cabo']} mm²")
    
    doc.add_heading("2. Detalhamento dos Circuitos Terminais (QGD)", level=2)
    for circ in circuitos:
        doc.add_paragraph(f"Circuito {circ['numero']} - {circ['nome']}\n"
                          f"Potência: {circ['potencia']:.0f} VA | Tensão Nominal: {circ['tensao']} V\n"
                          f"Corrente do Projeto (Ib): {circ['corrente']:.2f} A | Limite de Condução (Iz Corrigido): {circ['iz_corrigida']:.2f} A\n"
                          f"Condutor Selecionado: {circ['bitola']} mm² | Elemento de Proteção (Disjuntor): {circ['disjuntor']} A\n"
                          f"Queda de Tensão Final: {circ['queda_tensao']:.2f}% | Dispositivo Diferencial: {circ['dr']}")
    target = BytesIO()
    doc.save(target)
    return target.getvalue()
st.markdown("""
    <div style="background-color: #0f172a; padding: 24px; border-radius: 12px; margin-bottom: 30px; text-align: center; border: 1px solid #0284c7;">
        <div style="font-size: 40px; margin-bottom: 5px; text-shadow: 0 0 12px #0284c7;">⚡</div>
        <h1 style="margin: 0; font-size: 28px; font-weight: 800; letter-spacing: 2px; color: #ffffff;">RIBEIRO ELÉTRICA <span style="color: #0284c7;">PRO V2</span></h1>
        <div style="width: 60px; height: 3px; background: linear-gradient(90deg, #0369a1, #0284c7); margin: 12px auto; border-radius: 2px;"></div>
        <p style="margin: 0; color: #94a3b8; font-size: 13px; font-weight: 500; letter-spacing: 1px;">NBR 5410 & REQUISITOS MULTI-CONCESSIONÁRIAS ESTADUAIS</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("### 👤 Configurações do Projeto e Dados do Cliente")
c_cli1, c_cli2 = st.columns(2)
nome_cliente = c_cli1.text_input("Nome do Cliente", placeholder="Ex: Joao Silva")
endereco_obra = c_cli2.text_input("Endereço Completo da Obra", placeholder="Ex: Av. Atlântica, 1050")

c_prof1, c_prof2 = st.columns(2)
nome_responsavel = c_prof1.text_input("Responsável Técnico (Projetista)", placeholder="Ex: Eng. Pedro Santos")
registro_tecnico = c_prof2.text_input("Registro Técnico (CREA / CFT)", placeholder="Ex: 506.XXX")

st.markdown("#### 🏢 Enquadramento Geográfico / Concessionária de Energia")
estado_origem = st.selectbox(
    "Selecione o Estado da Obra para adequar o Padrão de Entrada:",
    ["São Paulo (SP) - ENEL SP", "São Paulo (SP) - CPFL Paulista", "Rio de Janeiro (RJ) - LIGHT", "Rio de Janeiro (RJ) - ENEL RJ", "Espírito Santo (ES) - EDP ES"]
)
inclui_padrao_entrada = st.checkbox("Incluir dimensionamento e detalhamento do Padrão de Entrada Geral", value=True)

st.markdown("---")
col_cadastro, col_projeto = st.columns([1.2, 1.4], gap="large")

with col_cadastro:
    st.markdown("### 📝 Cadastrar Novo Cômodo")
    
    opcoes_comodos = ["Sala", "Sala de Estar", "Quarto", "Suíte", "Corredor", "Banheiro", "Cozinha", "Área de Serviço", "Garagem", "Escritório", "Varanda"]
    nome_c = st.selectbox("Selecione o Ambiente:", opcoes_comodos)
    
    idx_tipo = 1 if nome_c in ["Cozinha", "Área de Serviço", "Banheiro"] else 0
    tipo_c = st.radio("Classificação do Ambiente:", ["Área Seca", "Área Úmida/Molhada"], index=idx_tipo)
    
    sugerir_suite = True if nome_c == "Suíte" else False
    possui_suite = st.checkbox("Este cômodo possui Banheiro Integrado (Configuração Suíte)?", value=sugerir_suite)
    
    # --- SISTEMA DE MEDIDAS PREDEFINIDAS + DIGITAÇÃO MANUAL ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        opcoes_larg = ["1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "5.0", "Outra (Digitar Manualmente)"]
        sel_larg = st.selectbox("Largura Padrão (m):", opcoes_larg, index=3)
        if sel_larg == "Outra (Digitar Manualmente)":
            larg_c = st.number_input("Digite a Largura (m):", min_value=0.1, value=3.0, step=0.1, key="larg_manual")
        else:
            larg_c = float(sel_larg)
            
    with c2:
        opcoes_comp = ["1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "5.0", "Outra (Digitar Manualmente)"]
        sel_comp = st.selectbox("Comprimento Padrão (m):", opcoes_comp, index=5)
        if sel_comp == "Outra (Digitar Manualmente)":
            comp_c = st.number_input("Digite o Comprimento (m):", min_value=0.1, value=4.0, step=0.1, key="comp_manual")
        else:
            comp_c = float(sel_comp)
            
    with c3:
        opcoes_dist = ["5", "10", "15", "20", "25", "30", "Outra (Digitar Manualmente)"]
        sel_dist = st.selectbox("Distância ao QGD (m):", opcoes_dist, index=2)
        if sel_dist == "Outra (Digitar Manualmente)":
            dist_c = st.number_input("Digite a Distância (m):", min_value=1.0, value=15.0, step=1.0, key="dist_manual")
        else:
            dist_c = float(sel_dist)
        
    tensao_c = st.selectbox("Tensão Base (Iluminação e TUGs)", (127, 220))
    agrup_c = st.number_input("Circuitos Agrupados no mesmo conduto", min_value=1, value=2, step=1)
    st.markdown("#### 🔌 Cargas Especiais / TUEs do Cômodo")
    equip_sugestao = st.selectbox(
        "Selecione a Carga Dedicada:",
        ["Nenhum / Selecione...", "Chuveiro Elétrico", "Ar Condicionado", "Lava e Seca", "Forno Elétrico", "Micro-ondas Grande", "Torneira Elétrica", "Outro (Manual)"]
    )
    
    opcoes_potencia = [0]
    fp_sugerido = 1.0
    tensao_sugerida = 220
    mostrar_manual = False
    
    if equip_sugestao == "Chuveiro Elétrico":
        opcoes_potencia = [4400, 5500, 6800, 7500]
        fp_sugerido = 1.0  
        tensao_sugerida = 220
    elif equip_sugestao == "Ar Condicionado":
        opcoes_potencia = [900, 1200, 1600, 2200]
        fp_sugerido = 0.80  
        tensao_sugerida = 220
    elif equip_sugestao == "Lava e Seca":
        opcoes_potencia = [2000, 2500, 3000]
        fp_sugerido = 0.85
        tensao_sugerida = 127
    elif equip_sugestao == "Forno Elétrico":
        opcoes_potencia = [1500, 2200, 3500]
        fp_sugerido = 1.0
        tensao_sugerida = 220
    elif equip_sugestao == "Micro-ondas Grande":
        opcoes_potencia = [1200, 1500, 1800]
        fp_sugerido = 0.90
        tensao_sugerida = 127
    elif equip_sugestao == "Torneira Elétrica":
        opcoes_potencia = [3500, 4500, 5500]
        fp_sugerido = 1.0
        tensao_sugerida = 220
    elif equip_sugestao == "Outro (Manual)":
        mostrar_manual = True

    col_tue_final, col_tue_v = st.columns([1.5, 0.7])
    
    with col_tue_final:
        if mostrar_manual:
            nome_tue = st.text_input("Nome da TUE:", placeholder="Ex: Hidromassagem")
            w_tue = st.number_input("Potência Ativa (W):", min_value=0, value=0, step=100)
            fp_tue = st.number_input("Fator de Potência (cos phi):", min_value=0.1, max_value=1.0, value=0.9)
        elif equip_sugestao != "Nenhum / Selecione...":
            nome_tue = equip_sugestao
            w_tue = st.selectbox("Escolha a Potência Comercial (W):", opcoes_potencia)
            fp_tue = fp_sugerido
        else:
            nome_tue, w_tue, fp_tue = "", 0, 1.0
            
    with col_tue_v:
        v_tue = st.selectbox("Tensão TUE (V)", (220, 127), index=0 if tensao_sugerida == 220 else 1) if equip_sugestao != "Nenhum / Selecione..." else 220

    if st.button("➕ Vincular TUE ao Ambiente"):
        if nome_tue and w_tue > 0:
            va_calculado = w_tue / fp_tue
            st.session_state.tues_temporarias.append({"equipamento": nome_tue, "potencia_w": w_tue, "potencia_va": va_calculado, "tensao": v_tue, "fp": fp_tue})
            st.toast(f"Carga '{nome_tue}' de {w_tue}W vinculada.")
            
    if st.session_state.tues_temporarias:
        st.write("**Cargas Especiais Vinculadas Provisoriamente:**")
        tues_para_remover = []
        for idx, t in enumerate(st.session_state.tues_temporarias):
            t_col1, t_col2 = st.columns([2, 0.5])
            t_col1.caption(f"• {t['equipamento']}: {t['potencia_w']}W | {t['potencia_va']:.0f}VA ({t['tensao']}V) FP: {t['fp']}")
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
            
            va_tugs_quarto = 0
            va_tugs_banheiro = 0
            
            if possui_suite:
                q_tugs_q = math.ceil(per_calc / 5)
                va_tugs_quarto = q_tugs_q * 100
                va_tugs_banheiro = 600
                is_molhada = False
            else:
                q_tugs = math.ceil(per_calc / 3.5) if is_molhada else math.ceil(per_calc / 5)
                va_tugs_quarto = ((3 * 600) + ((q_tugs - 3) * 100) if q_tugs > 3 else q_tugs * 600) if is_molhada else q_tugs * 100
                
            st.session_state.comodos.append({
                "nome": nome_c, "molhada": is_molhada, "largura": larg_c, "comprimento": comp_c,
                "area": area_calc, "perimetro": per_calc, "tensao": tensao_c, "distancia": dist_c,
                "va_ilum": va_ilum, "va_tugs": va_tugs_quarto, "agrupados": agrup_c,
                "is_suite": possui_suite, "va_banheiro": va_tugs_banheiro,
                "tues": list(st.session_state.tues_temporarias)
            })
            st.session_state.comodos_contagem[nome_c] = st.session_state.comodos_contagem.get(nome_c, 0) + 1
            st.session_state.comodos[-1]["nome"] = f"{nome_c} {st.session_state.comodos_contagem[nome_c]}"
            st.session_state.tues_temporarias = []
            st.rerun()

    if st.button("🗑️ Limpar Todo o Projeto", key="clear_all"):
        st.session_state.comodos = []
        st.session_state.tues_temporarias = []
        st.session_state.comodos_contagem = {}
        st.rerun()
with col_projeto:
    st.markdown("### 📋 Quadro de Distribuição & Análise Técnica")
    if not st.session_state.comodos:
        st.info("Nenhum ambiente adicionado. Preencha os dados e salve o primeiro cômodo.")
    else:
        circuitos = []
        c_num = 1
        
        for v in (127, 220):
            ilum_comodos = [c for c in st.session_state.comodos if c['tensao'] == v]
            if ilum_comodos:
                circuitos.append({
                    "numero": c_num, "nome": f"Iluminação Geral ({v}V)", "potencia": sum(c['va_ilum'] for c in ilum_comodos),
                    "tensao": v, "tipo": "ILUM", "dr": "RECOMENDADO", "distancia": max(c['distancia'] for c in ilum_comodos), "agrupados": max(c['agrupados'] for c in ilum_comodos)
                })
                c_num += 1
        
        for v in (127, 220):
            umidas = [c for c in st.session_state.comodos if c['tensao'] == v and c['molhada']]
            for u in umidas:
                circuitos.append({
                    "numero": c_num, "nome": f"TUGs Cozinha/Serviço - {u['nome']}", "potencia": u['va_tugs'],
                    "tensao": v, "tipo": "TUG", "dr": "OBRIGATÓRIO (DR)", "distancia": u['distancia'], "agrupados": u['agrupados']
                })
                c_num += 1
            
            suites = [c for c in st.session_state.comodos if c['tensao'] == v and c['is_suite']]
            for s in suites:
                circuitos.append({
                    "numero": c_num, "nome": f"TUG Banheiro - {s['nome']}", "potencia": s['va_banheiro'],
                    "tensao": v, "tipo": "TUG", "dr": "OBRIGATÓRIO (DR)", "distancia": s['distancia'], "agrupados": s['agrupados']
                })
                c_num += 1
            
            secas = [c for c in st.session_state.comodos if c['tensao'] == v and not c['molhada'] and not c['is_suite']]
            for s in suites:
                secas.append({"nome": f"Quarto {s['nome']}", "va_tugs": s['va_tugs'], "distancia": s['distancia'], "agrupados": s['agrupados']})
                
            c_nome, c_va, c_dist, c_agrup = [], 0, 0, 1
            limite = 1200 if v == 127 else 2500
            
            for s in secas:
                if c_va + s['va_tugs'] <= limite:
                    c_nome.append(s['nome'])
                    c_va += s['va_tugs']
                    c_dist = max(c_dist, s['distancia'])
                    c_agrup = max(c_agrup, s['agrupados'])
                else:
                    if c_va > 0:
                        circuitos.append({"numero": c_num, "nome": f"TUGs Secas Agrupadas ({', '.join(c_nome)})", "potencia": c_va, "tensao": v, "tipo": "TUG", "dr": "RECOMENDADO", "distancia": c_dist, "agrupados": c_agrup})
                        c_num += 1
                    c_nome, c_va, c_dist, c_agrup = [s['nome']], s['va_tugs'], s['distancia'], s['agrupados']
            if c_va > 0:
                circuitos.append({"numero": c_num, "nome": f"TUGs Secas Agrupadas ({', '.join(c_nome)})", "potencia": c_va, "tensao": v, "tipo": "TUG", "dr": "RECOMENDADO", "distancia": c_dist, "agrupados": c_agrup})
                c_num += 1

        for c in st.session_state.comodos:
            for t in c['tues']:
                circuitos.append({
                    "numero": c_num, "nome": f"TUE Exclusiva - {t['equipamento']} ({c['nome']})", "potencia": t['potencia_va'],
                    "potencia_w": t['potencia_w'], "tensao": t['tensao'], "tipo": "TUE", "dr": "OBRIGATÓRIO (DR)", "distancia": c['distancia'], "agrupados": c['agrupados']
                })
                c_num += 1

        pot_ilum_tug_w = sum(circ['potencia'] * 0.8 for circ in circuitos if circ['tipo'] != "TUE") 
        pot_tue_w = sum(circ.get('potencia_w', circ['potencia']) for circ in circuitos if circ['tipo'] == "TUE")
        
        if pot_ilum_tug_w <= 1000: fd_ilum = 0.86
        elif pot_ilum_tug_w <= 2000: fd_ilum = 0.75
        elif pot_ilum_tug_w <= 5000: fd_ilum = 0.52
        elif pot_ilum_tug_w <= 8000: fd_ilum = 0.40
        else: fd_ilum = 0.35
        
        num_tues = len([circ for circ in circuitos if circ['tipo'] == "TUE"])
        if num_tues <= 1: fd_tue = 1.0
        elif num_tues == 2: fd_tue = 0.84
        elif num_tues == 3: fd_tue = 0.76
        elif num_tues == 4: fd_tue = 0.68
        else: fd_tue = 0.55
        
        demanda_total_w = (pot_ilum_tug_w * fd_ilum) + (pot_tue_w * fd_tue)
        demanda_kva = (demanda_total_w / 0.92) / 1000  
        
        if "ENEL SP" in estado_origem or "CPFL" in estado_origem:
            lim_mono, lim_bi = 12.0, 25.0
        elif "LIGHT" in estado_origem or "ENEL RJ" in estado_origem:
            lim_mono, lim_bi = 10.0, 20.0
        else:  
            lim_mono, lim_bi = 15.0, 30.0

        if demanda_kva <= lim_mono:
            padrao = {"tipo": "Monofásico", "disjuntor": 40, "cabo": 10.0, "demanda_kva": demanda_kva}
        elif demanda_kva <= lim_bi:
            padrao = {"tipo": "Bifásico", "disjuntor": 50, "cabo": 16.0, "demanda_kva": demanda_kva}
        else:
            padrao = {"tipo": "Trifásico", "disjuntor": 63, "cabo": 25.0, "demanda_kva": demanda_kva}
        resumo_disjuntores = {}
        resumo_cabos = {1.5: 0.0, 2.5: 0.0, 4.0: 0.0, 6.0: 0.0, 10.0: 0.0, 16.0: 0.0}

        for circ in circuitos:
            circ['corrente'] = circ['potencia'] / circ['tensao']
            f_agrup = 1.0 if circ['agrupados'] == 1 else 0.80 if circ['agrupados'] == 2 else 0.70 if circ['agrupados'] == 3 else 0.65
            b_final = 1.5 if circ['tipo'] == "ILUM" else 2.5 
            
            while True:
                cap_base = 17.5 if b_final==1.5 else 24.0 if b_final==2.5 else 32.0 if b_final==4.0 else 41.0 if b_final==6.0 else 57.0 if b_final==10.0 else 76.0
                cap_corrigida = cap_base * f_agrup
                q_v = (2.0 * 0.0178 * circ['distancia'] * circ['corrente']) / b_final
                pct = (q_v / circ['tensao']) * 100.0
                
                if circ['corrente'] <= cap_corrigida and pct <= 4.0:
                    circ['bitola'] = b_final
                    circ['queda_tensao'] = pct
                    circ['iz_corrigida'] = cap_corrigida
                    break
                else:
                    secoes_superiores = {1.5: 2.5, 2.5: 4.0, 4.0: 6.0, 6.0: 10.0, 10.0: 16.0}
                    b_final = secoes_superiores.get(b_final, 16.0)
                    if b_final == 16.0:
                        circ['bitola'] = 16.0
                        circ['queda_tensao'] = pct
                        circ['iz_corrigida'] = cap_corrigida
                        break

            i_proj = circ['corrente']
            disjuntores_din = [10, 16, 20, 25, 32, 40, 50, 63]
            dj_adequado = 10
            for d in disjuntores_din:
                if d >= i_proj and d <= circ['iz_corrigida']:
                    dj_adequado = d
                    break
                elif d >= i_proj:
                    dj_adequado = d  
            
            circ['disjuntor'] = dj_adequado
            resumo_disjuntores[dj_adequado] = resumo_disjuntores.get(dj_adequado, 0) + 1
            resumo_cabos[circ['bitola']] = resumo_cabos.get(circ['bitola'], 0.0) + (circ['distancia'] * 3.0) 

        v_aba, d_aba, mat_aba = st.tabs(["🏠 Ambientes Salvos", "🗂️ QGD Final Otimizado", "📦 Lista Técnica de Materiais"])
        
        with v_aba:
            comodo_remover = None
            for idx, co in enumerate(st.session_state.comodos):
                with st.expander(f"📍 {co['nome'].upper()}"):
                    st.write(f"Área Útil: {co['area']:.2f} m² | Perímetro: {co['perimetro']:.1f} m")
                    st.write(f"Iluminação Calculada: {co['va_ilum']} VA | TUGs Gerais: {co['va_tugs']} VA")
                    if co["tues"]:
                        st.caption("**Cargas Especiais Vinculadas Integradas:**")
                        for tu in co["tues"]:
                            st.caption(f"  - {tu['equipamento']}: {tu['potencia_w']}W ({tu['tensao']}V)")
                    if st.button("Excluir Cômodo", key=f"del_comodo_{idx}"):
                        comodo_remover = idx
            if comodo_remover is not None:
                st.session_state.comodos.pop(comodo_remover)
                st.rerun()

        with d_aba:
            if inclui_padrao_entrada:
                st.markdown(f"#### 🏢 Entrada Geral Recomendada: **{padrao['tipo']}**")
                st.markdown(f"**Demanda Projetada:** {padrao['demanda_kva']:.2f} kVA | **Disjuntor Geral:** {padrao['disjuntor']}A | **Cabo Principal:** {padrao['cabo']} mm²")
                st.caption(f"Cálculo executado com as curvas de simultaneidade exigidas para a região da {estado_origem}.")
                st.markdown("---")
            
            for circ in circuitos:
                st.markdown(f"""
                <div style="border:1px solid #1e293b; padding:14px; border-radius:8px; margin-bottom:12px; background-color:#1e222b;">
                    <h5 style="margin:0; color:#38bdf8;">Circuito {circ['numero']} - {circ['nome']}</h5>
                    <p style="margin:3px 0; font-size:13px;"><b>Condutor Recomendado:</b> {circ['bitola']} mm² | <b>Disjuntor Termomagnético:</b> {circ['disjuntor']} A DIN</p>
                    <p style="margin:3px 0; font-size:12px; color:#94a3b8;">Queda de Tensão Final: {circ['queda_tensao']:.2f}% | Segurança Diferencial (Fuga): {circ['dr']}</p>
                </div>
                """, unsafe_allow_html=True)
                
        with mat_aba:
            st.markdown("#### 🛒 Quantitativo Estimado de Compras")
            if inclui_padrao_entrada:
                st.write(f"• Condutor de Cobre de Entrada Geral ({padrao['cabo']} mm²): **15.0 metros**")
                st.write(f"• Disjuntor Caixa Moldada / DIN Geral {padrao['disjuntor']}A: **1 un.**")
            for amp, quant in sorted(resumo_disjuntores.items()):
                st.write(f"• Disjuntor Termomagnético Monopolar DIN {amp}A: **{quant} un.**")
            for bit, metros in sorted(resumo_cabos.items()):
                if metros > 0:
                    st.write(f"• Cabo Flexível Isolado {bit} mm² (Fase/Neutro/Terra Acumulados): **{metros:.1f} metros**")

        st.markdown("---")
        st.markdown("#### 📂 Emissão de Relatórios Oficiais")
        c_down1, c_down2 = st.columns(2)
        with c_down1:
            dados_pdf = gerar_pdf(nome_cliente, endereco_obra, nome_responsavel, registro_tecnico, estado_origem, circuitos, padrao, inclui_padrao_entrada)
            st.download_button(label="📥 BAIXAR LAUDO TÉCNICO COMPLETO (PDF)", data=dados_pdf, file_name="laudo_tecnico_eletrico.pdf", mime="application/pdf")
        with c_down2:
            dados_word = gerar_word(nome_cliente, endereco_obra, nome_responsavel, registro_tecnico, estado_origem, circuitos, padrao, inclui_padrao_entrada)
            st.download_button(label="📝 BAIXAR MEMORIAL DESCRITIVO (WORD)", data=dados_word, file_name="memorial_eletrico.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
