import streamlit as st

# Configurazione della pagina per mobile e desktop
st.set_page_config(
    page_title="Configuratore Ingressi PLC",
    page_icon="⚡",
    layout="centered"
)

# Stile CSS personalizzato per migliorare la leggibilità su smartphone
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Electrex")
st.info("Calcolo parametri di configurazione per ingressi analogici e digitali.")

# Creazione delle schede (Tabs)
tab_ana, tab_dig = st.tabs(["📉 Analogica", "🔢 Digitale"])

# --- SCHEDA ANALOGICA ---
with tab_ana:
    st.header("Condizionamento Segnale")
    
    with st.expander("Parametri e Scala", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            r = st.number_input("Resistenza (Ohm)", value=200.0, step=0.1, help="Resistenza di shunt")
            ma_min = st.number_input("Corrente Min (mA)", value=4.0, step=0.1)
            ma_max = st.number_input("Corrente Max (mA)", value=20.0, step=0.1)
        with col2:
            s_min = st.number_input("Inizio Scala (Smin)", value=0.0, step=1.0)
            s_max = st.number_input("Fondo Scala (Smax)", value=2000.0, step=1.0)

    with st.expander("Parametri Integrazione"):
        col3, col4 = st.columns(2)
        with col3:
            u_in_tempo = st.selectbox("Base Tempo Ingresso", ["ora (h)", "minuto (min)", "secondo (s)"])
            u_in_scala = st.selectbox("Scala Unità Ingresso", ["Wh / l / g", "kWh / mc / kg", "MWh / t"], index=1)
        with col4:
            u_out_scala = st.selectbox("Scala Totale Desiderata", ["Wh / l / g", "kWh / mc / kg", "MWh / t"], index=1)

    if st.button("CALCOLA ANALOGICA"):
        try:
            v_min = r * ma_min / 1000
            v_max = r * ma_max / 1000
            
            # Formule dal file originale
            ana_guadagno = (s_max - s_min) / (v_max - v_min)
            ana_offset = (s_min * (1 / ana_guadagno)) - v_min
            ana_cutoff = (10000 / 24) * v_min
            
            # Calcolo guadagno integratore
            basi_tempo = {"ora (h)": 1, "minuto (min)": 60, "secondo (s)": 3600}
            scale_conv = {"Wh / l / g": 0.001, "kWh / mc / kg": 1.0, "MWh / t": 1000.0}
            
            k_tempo = basi_tempo[u_in_tempo]
            k_conv = scale_conv[u_in_scala] / scale_conv[u_out_scala]
            int_guadagno = k_tempo * k_conv
            
            st.subheader("Risultati Analogica")
            res_col1, res_col2 = st.columns(2)
            res_col1.metric("Guadagno", f"{ana_guadagno:.4f}")
            res_col1.metric("Offset", f"{ana_offset:.4f}")
            res_col2.metric("Cutoff (Soglia)", f"{int(ana_cutoff)}")
            res_col2.metric("Guadagno Integratore", f"{int_guadagno:.4f}")
        except Exception as e:
            st.error(f"Errore nei calcoli: {e}")

# --- SCHEDA DIGITALE ---
with tab_dig:
    st.header("Calcolo parametri")
    
    u_nome = st.text_input("Unità di misura (es. mc, litri, kg, kWh)", "kWh")
    
    with st.expander("Rapporti e Costanti", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            ta_p = st.number_input("TA Primario", value=100, min_value=1.0)
            ta_s = st.number_input("TA Secondario", value=5, min_value=1.0)
        with c2:
            tv_p = st.number_input("TV Primario", value=15000, min_value=1.0)
            tv_s = st.number_input("TV Secondario", value=100, min_value=1.0)
            
    with st.expander("Dati Processo"):
        imp_unita = st.number_input(f"Impulsi per {u_nome}", value=10000)
        val_ist = st.number_input(f"Valore Istantaneo ({u_nome}/h)", value=1000)
        t_deriv_min = st.number_input("Finestra Derivata (minuti)", value=1)
        
    # Funzionalità richiesta: conversione peso in uscita
    sc_dig_out = st.selectbox(
        "Converti in:", 
        ["Millesimi (es. litri, grammi, Wh)", "Unità Base (es. mc, kg, kWh)", "Migliaia (es. tonnellate, MWh)"],
        index=1
    )

    if st.button("CALCOLA DIGITALE"):
        try:
            k_tot = (ta_p / ta_s) * (tv_p / tv_s)
            peso_base = k_tot / imp_unita
            
            # Mappa scale per conversione peso
            map_dig = {
                "Millesimi (es. litri, grammi, Wh)": 0.001,
                "Unità Base (es. mc, kg, kWh)": 1.0,
                "Migliaia (es. tonnellate, MWh)": 1000.0
            }
            # Se l'utente vuole l'uscita in millesimi (0.001), il numero deve essere moltiplicato (1/0.001)
            peso_finale = peso_base / map_dig[sc_dig_out]
            
            # Calcolo frequenza e tempi
            if val_ist > 0:
                freq_hz = val_ist / (peso_base * 3600)
                periodo_ms = (1 / freq_hz) * 1000
                t_on_off = periodo_ms / 2
            else:
                freq_hz = periodo_ms = t_on_off = 0.0
            
            # Calcolo Derivata
            quantita_periodo = (val_ist / 60) * t_deriv_min
            
            st.subheader("Risultati Digitale")
            r_col1, r_col2 = st.columns(2)
            
            r_col1.write(f"**Rapporto K:** {k_tot:.2f}")
            r_col1.error(f"**Peso Impulso:** {peso_finale:.6f}")
            r_col1.write(f"**Frequenza:** {freq_hz:.4f} Hz")
            
            r_col2.write(f"**Periodo:** {periodo_ms:.2f} ms")
            r_col2.write(f"**Tempo ON/OFF:** {t_on_off:.2f} ms")
            r_col2.warning(f"**Derivata Oraria:** {val_ist:.2f} {u_nome}/h")
            
            st.info(f"Quantità accumulata in {t_deriv_min} min: {quantita_periodo:.4f} {u_nome}")
            
        except Exception as e:
            st.error(f"Errore: {e}")