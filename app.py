import streamlit as st
import pandas as pd
import json
import os
import hashlib
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Reserva Laboratorio de Movimiento", page_icon="📅", layout="wide")

SPREADSHEET_ID = "17WgwdmnjdQ6D5rgQ32FSzR8ono6M7r9qH6WeuTz2w1M"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gsheet():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    client = gspread.authorize(creds)
    sh = client.open_by_key(SPREADSHEET_ID)
    try:
        ws = sh.worksheet("datos")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title="datos", rows=10, cols=2)
        ws.update("A1", [["reservas_db", "users_db"]])
        ws.update("A2", [[json.dumps({"CADI": {}, "FACSA": {}}), json.dumps({})]])
    return ws

def load_sheet_data():
    ws = get_gsheet()
    vals = ws.row_values(2)
    try:
        reservas = json.loads(vals[0]) if len(vals) > 0 and vals[0] else {"CADI": {}, "FACSA": {}}
    except:
        reservas = {"CADI": {}, "FACSA": {}}
    try:
        users = json.loads(vals[1]) if len(vals) > 1 and vals[1] else {}
    except:
        users = {}
    return reservas, users

def save_reservas(data):
    ws = get_gsheet()
    ws.update("A2", [[json.dumps(data)]])

def save_users(data):
    ws = get_gsheet()
    ws.update("B2", [[json.dumps(data)]])

# --- CONFIGURACIÓN DE ACCESO ---
ADMIN_EMAIL = "felipe.retamal@umag.cl"

ALLOWED_USERS = {
    "nelson.mcardle@umag.cl": "Nelson Mc Ardle Draguicevic",
    "alejandra.fernandez@umag.cl": "Alejandra Fernandez Elgueta",
    "carlos.carcamo@umag.cl": "Carlos Cárcamo Alvarado",
    "carolina.martinez@umag.cl": "Carolina Martínez A.",
    "pedro.quintana@umag.cl": "Pedro Quintana P.",
    "felipe.retamal@umag.cl": "Felipe Retamal",
    "ruben.reyes@umag.cl": "Ruben Reyes S.",
    "romy.barrientos@umag.cl": "Romy Barrientos Ortega",
    "sergio.cares@umag.cl": "Sergio Cares B.",
    "solange.araya@umag.cl": "Solange Macarena Araya Albornoz",
    "agostina.gallardo@umag.cl": "Agostina M. Gallardo",
    "leslie.oliarte@umag.cl": "Leslie Oliarte",
    "nazareth.yanez@umag.cl": "Nazareth Yáñez Ulloa",
    "rene.hernandez@umag.cl": "René Hernández Delgado",
    "sebastian.almonacid@umag.cl": "Sebastián Almonacid",
    "pablo.rivera@umag.cl": "PABLO ANDRÉS RIVERA MIRANDA",
    "natalia.suazo@umag.cl": "Natalia Alejandra Suazo Paredes"
}

blocks = [
    "08:00 - 09:30",
    "09:30 - 11:10",
    "11:10 - 12:40",
    "12:40 - 14:30",
    "14:30 - 16:10",
    "16:10 - 17:50",
    "17:50 - 19:20"
]

days_of_week = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]



def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

reservas_db, users_db = load_sheet_data()

if "CADI" not in reservas_db: reservas_db["CADI"] = {}
if "FACSA" not in reservas_db: reservas_db["FACSA"] = {}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.session_state.name = ""

def login_user(email, password):
    email = email.lower().strip()
    if email in users_db and users_db[email]['password'] == hash_pass(password):
        st.session_state.logged_in = True
        st.session_state.email = email
        st.session_state.name = users_db[email]['name']
        st.rerun()
    else:
        st.error("❌ Correo o contraseña incorrectos.")

def register_user(email, password):
    email = email.lower().strip()
    if not email or not password:
        st.error("⚠️ El correo y contraseña no pueden estar vacíos")
        return
    if email not in ALLOWED_USERS:
        st.error("❌ Acceso Denegado. Solo correos autorizados de Kinesiología.")
        return
    if email in users_db:
        st.error("❌ El correo ya está registrado. Inicia sesión.")
    else:
        users_db[email] = {
            "password": hash_pass(password),
            "name": ALLOWED_USERS[email]
        }
        save_users(users_db)
        st.success(f"✅ Cuenta creada con éxito para {ALLOWED_USERS[email]}.")

if not st.session_state.logged_in:
    st.title("🔐 Acceso al Sistema de Reservas")
    st.markdown("Plataforma exclusiva para Docentes de Kinesiología y el Laboratorio de Análisis de Movimiento (UMAG).")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Acceder")
        with st.form("login_form"):
            l_email = st.text_input("Correo Institucional (@umag.cl)")
            l_pass = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar"):
                login_user(l_email, l_pass)
    with col2:
        st.subheader("Crear Mi Cuenta")
        with st.form("register_form"):
            r_email = st.text_input("Correo Institucional (@umag.cl)")
            r_pass = st.text_input("Crea una Contraseña a tu elección", type="password")
            if st.form_submit_button("Registrarse"):
                register_user(r_email, r_pass)
else:
    @st.dialog("Confirmar Reservas")
    def confirm_dialog(dates_to_book, blocks_to_book, actividad, allow_shared, max_extra):
        act_lab = st.session_state.selected_lab
        total = len(dates_to_book) * len(blocks_to_book)
        st.warning(f"Estás a punto de registrar **{total}** bloques horarios en el sistema.")
        st.write(f"- **Laboratorio:** {act_lab}")
        st.write(f"- **Días seleccionados:** {len(dates_to_book)}")
        st.write(f"- **Actividad:** {actividad}")
        if allow_shared:
            st.write(f"- **Modo:** Compartido (+{max_extra} docentes max)")
        else:
            st.write(f"- **Modo:** Exclusivo (No compartir)")
            
        st.write("¿Confirmas esta asignación en el calendario?")
        col1, col2 = st.columns(2)
        if col1.button("✅ Sí, Confirmar", use_container_width=True):
            count_reservas = 0
            for d_obj in dates_to_book:
                d_str = d_obj.strftime("%Y-%m-%d")
                if d_str not in reservas_db[act_lab]:
                    reservas_db[act_lab][d_str] = {}
                for b in blocks_to_book:
                    new_booking = {
                        "display": f"{st.session_state.name} ({actividad})",
                        "owner_email": st.session_state.email
                    }
                    if b not in reservas_db[act_lab][d_str]:
                        reservas_db[act_lab][d_str][b] = {
                            "shared": allow_shared,
                            "max_extra": max_extra if allow_shared else 0,
                            "bookings": [new_booking]
                        }
                    else:
                        reservas_db[act_lab][d_str][b]["bookings"].append(new_booking)
                    count_reservas += 1
                    
            save_reservas(reservas_db)
            st.session_state.success_msg = f"✅ Éxito: Se reservaron {count_reservas} bloques en {act_lab}."
            st.rerun()
            
        if col2.button("❌ Cancelar", use_container_width=True):
            st.rerun()

    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())

    is_admin = (st.session_state.email == ADMIN_EMAIL)
    badge = "👑 Administrador" if is_admin else "👨‍🏫 Docente"

    if 'selected_lab' not in st.session_state:
        st.session_state.selected_lab = None

    if st.session_state.selected_lab is None:
        st.title("🏛️ Portal de Reservas de Laboratorios UMAG")
        st.markdown(f"👋 Bienvenido/a, **{st.session_state.name}** | {badge}")
        st.write("Selecciona una de las siguientes opciones para continuar:")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.container(border=True):
                st.info("### 🏃‍♂️ CADI\n**Análisis de Movimiento Humano**")
                st.caption("Ubicado en el CADI UMAG.")
                if st.button("Ingresar a CADI", use_container_width=True, type="primary"):
                    st.session_state.selected_lab = "CADI"
                    st.rerun()
                
        with col2:
            with st.container(border=True):
                st.success("### 🩺 Cs. de la Salud\n**Laboratorio de Kinesiología**")
                st.caption("Ubicado en la Facultad de Cs. de la Salud.")
                if st.button("Ingresar a Cs. de la Salud", use_container_width=True, type="primary"):
                    st.session_state.selected_lab = "FACSA"
                    st.rerun()
                
        with col3:
            with st.container(border=True):
                st.warning("### 🤔 Indiferente\n**Asistente Inteligente**")
                st.caption("Buscador de disponibilidad global.")
                if st.button("Buscar Disponibilidad", use_container_width=True, type="primary"):
                    st.session_state.show_recommender = True
                    st.rerun()
                
        if st.session_state.get("show_recommender", False):
            st.divider()
            st.subheader("Buscador Inteligente")
            st.write("Dinos qué horario necesitas y el sistema buscará en ambos recintos simultáneamente para ofrecerte la mejor opción.")
            
            with st.container(border=True):
                rec_date = st.date_input("¿Para qué día necesitas el laboratorio?", value=today, format="DD/MM/YYYY")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    rec_start = st.selectbox("Desde bloque:", blocks, key="rec_s")
                with col_r2:
                    rec_end = st.selectbox("Hasta bloque (Inclusivo):", blocks, key="rec_e")
                
                idx_s = blocks.index(rec_start)
                idx_e = blocks.index(rec_end)
                
                if st.button("🔎 Encontrar Laboratorio Libre"):
                    if idx_e < idx_s:
                        st.session_state.rec_result = "error_rango"
                    else:
                        bloques_req = blocks[idx_s:idx_e+1]
                        fecha_str = rec_date.strftime("%Y-%m-%d")
                        
                        cadi_free = True
                        for b in bloques_req:
                            if fecha_str in reservas_db["CADI"] and b in reservas_db["CADI"][fecha_str]:
                                b_data = reservas_db["CADI"][fecha_str][b]
                                if not b_data.get("shared", False) or len(b_data.get("bookings", [])) >= 1 + b_data.get("max_extra", 0):
                                    cadi_free = False
                                    break
                                    
                        facsa_free = True
                        for b in bloques_req:
                            if fecha_str in reservas_db["FACSA"] and b in reservas_db["FACSA"][fecha_str]:
                                b_data = reservas_db["FACSA"][fecha_str][b]
                                if not b_data.get("shared", False) or len(b_data.get("bookings", [])) >= 1 + b_data.get("max_extra", 0):
                                    facsa_free = False
                                    break
                        
                        # Store results in session_state so they persist across reruns
                        if cadi_free and facsa_free:
                            st.session_state.rec_result = "both"
                        elif cadi_free:
                            st.session_state.rec_result = "cadi"
                        elif facsa_free:
                            st.session_state.rec_result = "facsa"
                        else:
                            st.session_state.rec_result = "none"

            # ---- Mostrar resultado FUERA del if-button para que los botones funcionen ----
            rec_result = st.session_state.get("rec_result")
            if rec_result == "error_rango":
                st.error("El bloque de fin no puede ser anterior al de inicio.")
            elif rec_result == "both":
                st.success("✅ **Ambos laboratorios** tienen disponibilidad completa para tu solicitud.")
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("Reservar en CADI", key="btn_cadi_both", type="primary", use_container_width=True):
                    st.session_state.selected_lab = "CADI"
                    st.session_state.show_recommender = False
                    st.session_state.rec_result = None
                    st.session_state.menu_preselect = "Nueva Reserva"
                    st.rerun()
                if c_btn2.button("Reservar en Cs. de la Salud", key="btn_facsa_both", type="primary", use_container_width=True):
                    st.session_state.selected_lab = "FACSA"
                    st.session_state.show_recommender = False
                    st.session_state.rec_result = None
                    st.session_state.menu_preselect = "Nueva Reserva"
                    st.rerun()
            elif rec_result == "cadi":
                st.success("✅ Estás de suerte: El **Laboratorio CADI** tiene todo despejado para ti.")
                if st.button("Ir a Reservar en CADI", key="btn_cadi_only", type="primary", use_container_width=True):
                    st.session_state.selected_lab = "CADI"
                    st.session_state.show_recommender = False
                    st.session_state.rec_result = None
                    st.session_state.menu_preselect = "Nueva Reserva"
                    st.rerun()
            elif rec_result == "facsa":
                st.success("✅ Estás de suerte: El **Laboratorio de Cs. de la Salud** tiene todo despejado para ti.")
                if st.button("Ir a Reservar en Cs. de la Salud", key="btn_facsa_only", type="primary", use_container_width=True):
                    st.session_state.selected_lab = "FACSA"
                    st.session_state.show_recommender = False
                    st.session_state.rec_result = None
                    st.session_state.menu_preselect = "Nueva Reserva"
                    st.rerun()
            elif rec_result == "none":
                st.error("❌ Ningún laboratorio tiene disponibilidad completa para ese horario. Intenta elegir menos bloques, o comunícate con los docentes que ya han agendado para ver si aceptan compartir el recinto.")
        
        with st.sidebar:
            # Logos Institucionales
            if os.path.exists("logo_kine.png"):
                st.image("logo_kine.png", use_container_width=True)
            if os.path.exists("logo_kren.png"):
                st.image("logo_kren.png", use_container_width=True)
            
            if st.button("Cerrar Sesión"):
                st.session_state.logged_in = False
                st.session_state.email = ""
                st.session_state.name = ""
                st.session_state.show_recommender = False
                st.rerun()
        st.stop()

    titulo_lab = "Análisis de Movimiento Humano (CADI UMAG)" if st.session_state.selected_lab == "CADI" else "Kinesiología (Fac. Cs. de la Salud)"
    st.title("📅 Reserva Laboratorio de " + titulo_lab)
    st.markdown(f"👋 Bienvenido/a, **{st.session_state.name}** | {badge}")

    with st.sidebar:
        # Logos Institucionales
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            if os.path.exists("logo_kine.png"):
                st.image("logo_kine.png", use_container_width=True)
        with col_l2:
            if os.path.exists("logo_kren.png"):
                st.image("logo_kren.png", use_container_width=True)
                
        st.header("🏢 " + ("CADI" if st.session_state.selected_lab == "CADI" else "Cs. de la Salud"))
        if st.button("🏠 Volver al Menú Principal", use_container_width=True):
            st.session_state.selected_lab = None
            st.rerun()
        st.divider()
        
        if 'success_msg' in st.session_state:
            st.success(st.session_state.success_msg)
            del st.session_state.success_msg
            
        opciones_menu = ["Nueva Reserva", "Mis Reservas"]
        if is_admin: opciones_menu.append("Panel de Administración")
        opciones_menu.append("Cerrar Sesión")
        
        # Si venimos desde el recomendador, preseleccionar "Nueva Reserva"
        default_idx = 0
        if st.session_state.get("menu_preselect"):
            try:
                default_idx = opciones_menu.index(st.session_state.menu_preselect)
            except ValueError:
                default_idx = 0
            del st.session_state.menu_preselect
        
        modo = st.radio("Menú de Acciones", opciones_menu, index=default_idx)
        
        if modo == "Cerrar Sesión":
            st.session_state.logged_in = False
            st.session_state.email = ""
            st.session_state.name = ""
            st.rerun()
            
        elif modo == "Nueva Reserva":
            st.header("📝 Nueva Reserva")
            tipo_reserva = st.radio("Tipo de Reserva", ["Día Específico", "Recurrente (Múltiples Semanas)"], horizontal=True)
            
            with st.form("reserva_form"):
                if tipo_reserva == "Día Específico":
                    selected_date = st.date_input("Fecha de Reserva", value=today, format="DD/MM/YYYY")
                    dates_to_book = [selected_date]
                else:
                    col_s, col_e = st.columns(2)
                    with col_s: start_date = st.date_input("Desde:", value=today, format="DD/MM/YYYY")
                    with col_e: end_date = st.date_input("Hasta:", value=today + timedelta(days=30), format="DD/MM/YYYY")
                    
                    selected_weekdays = st.multiselect(
                        "Días de la semana", 
                        options=range(7), 
                        format_func=lambda x: days_of_week[x],
                        default=[today.weekday()]
                    )
                    
                    dates_to_book = []
                    if start_date <= end_date and selected_weekdays:
                        current_d = start_date
                        while current_d <= end_date:
                            if current_d.weekday() in selected_weekdays:
                                dates_to_book.append(current_d)
                            current_d += timedelta(days=1)
                
                st.write("Rango Horario:")
                col_b1, col_b2 = st.columns(2)
                with col_b1: block_inicio = st.selectbox("Bloque Inicio", blocks, index=0)
                with col_b2: block_fin = st.selectbox("Bloque Fin (Inclusivo)", blocks, index=0)
                idx_ini = blocks.index(block_inicio)
                idx_fin = blocks.index(block_fin)
                
                actividad = st.text_input("Actividad Corta", placeholder="Ej: FDE, MIND fit")
                
                # SHARING OPTIONS
                st.write("Configuración de Laboratorio Compartido:")
                allow_shared_str = st.radio("¿Permites que otras actividades se realicen en paralelo con la tuya?", ["No (Uso Exclusivo)", "Sí (Compartido)"])
                allow_shared = (allow_shared_str == "Sí (Compartido)")
                
                max_extra = 0
                if allow_shared:
                    max_extra = st.number_input("¿Cuántas actividades extras permites sumarse?", min_value=1, max_value=2, value=1)
                
                st.caption("Nota: Si te sumas a un bloque que ya tiene dueños, te adaptarás a sus reglas de compartición sin reemplazarlas.")

                submit = st.form_submit_button("Confirmar Reserva Múltiple" if len(dates_to_book)>1 or idx_fin>idx_ini else "Confirmar Reserva")
                
                if submit:
                    if not actividad:
                        st.error("⚠️ Debes indicar una Actividad.")
                    elif idx_fin < idx_ini:
                        st.error("⚠️ El bloque de fin NO puede ser antes que el bloque de inicio.")
                    elif not dates_to_book:
                        st.error("⚠️ No hay fechas válidas en el rango seleccionado.")
                    else:
                        blocks_to_book = blocks[idx_ini:idx_fin+1]
                        
                        # VERIFICATION PASS
                        conflictos = []
                        act_lab = st.session_state.selected_lab
                        for d_obj in dates_to_book:
                            d_str = d_obj.strftime("%Y-%m-%d")
                            for b in blocks_to_book:
                                if d_str in reservas_db[act_lab] and b in reservas_db[act_lab][d_str]:
                                    b_data = reservas_db[act_lab][d_str][b]
                                    # Verification Rules
                                    if not b_data.get("shared", False):
                                        conflictos.append(f"{d_str} ({b}) - Ya ocupado como Exclusivo")
                                    elif len(b_data.get("bookings", [])) >= 1 + b_data.get("max_extra", 0):
                                        conflictos.append(f"{d_str} ({b}) - Capacidad al límite")
                                    elif any(bk.get("owner_email") == st.session_state.email for bk in b_data.get("bookings", [])):
                                        conflictos.append(f"{d_str} ({b}) - Ya estás registrado aquí")
                        
                        if conflictos:
                            st.error("❌ Conflicto detectado. No se puede guardar:")
                            for c in conflictos[:5]: 
                                st.write(f"- {c}")
                            if len(conflictos) > 5:
                                st.write(f"...y {len(conflictos)-5} más.")
                            st.warning("Verifica el calendario. Si el laboratorio está exclusivo o lleno, no puedes sobreponer tu actividad.")
                        else:
                            confirm_dialog(dates_to_book, blocks_to_book, actividad, allow_shared, max_extra)

        elif modo == "Mis Reservas":
            act_lab = st.session_state.selected_lab
            act_lab_str = "CADI" if act_lab == "CADI" else "Cs. de la Salud"
            st.header(f"🗑️ Mis Reservas Activas en {act_lab_str}")
            
            user_reservas = []
            for d_str, day_blocks in reservas_db[act_lab].items():
                for b_time, b_data in day_blocks.items():
                    for idx_b, bk in enumerate(b_data.get("bookings", [])):
                        if bk.get("owner_email") == st.session_state.email:
                            user_reservas.append({
                                "date": d_str,
                                "date_obj": datetime.strptime(d_str, "%Y-%m-%d"),
                                "block": b_time, 
                                "display": bk.get("display"),
                                "booking_idx": idx_b
                            })
            
            if not user_reservas:
                st.info("No tienes reservas activas vinculadas a tu cuenta.")
            else:
                st.write("Selecciona cómo deseas eliminar tus reservas:")
                tab1, tab2, tab3 = st.tabs(["Eliminación Individual", "Por Rango de Fechas", "Por Mes Completo"])
                
                with tab1:
                    user_reservas_sorted = sorted(user_reservas, key=lambda x: (x["date"], x["block"]))
                    grouped = {}
                    for r in user_reservas_sorted:
                        grouped.setdefault(r["date"], []).append(r)
                    
                    for date_key, items in grouped.items():
                        fecha_str = datetime.strptime(date_key, '%Y-%m-%d').strftime('%d/%m/%Y')
                        with st.expander(f"📅 Fecha: {fecha_str}"):
                            for i, r in enumerate(items):
                                col_txt, col_btn = st.columns([3, 1])
                                with col_txt: st.write(f"**{r['block']}** - {r['display']}")
                                with col_btn:
                                    if st.button("Liberar Bloque", key=f"del_{r['date']}_{r['block']}_{r['booking_idx']}_{i}"):
                                        # Remove just this user's booking from the array
                                        target_arr = reservas_db[act_lab][r["date"]][r["block"]]["bookings"]
                                        # Find the exact match
                                        for k, entry in enumerate(target_arr):
                                            if entry["owner_email"] == st.session_state.email and entry["display"] == r["display"]:
                                                target_arr.pop(k)
                                                break
                                        
                                        # Clean block if nobody is left
                                        if not target_arr:
                                            del reservas_db[act_lab][r["date"]][r["block"]]
                                        if not reservas_db[act_lab][r["date"]]:
                                            del reservas_db[act_lab][r["date"]]
                                            
                                        save_reservas(reservas_db)
                                        st.rerun()
                
                with tab2:
                    st.info("Elimina de manera masiva.")
                    col_d1, col_d2 = st.columns(2)
                    with col_d1: del_start = st.date_input("Eliminar Desde:", format="DD/MM/YYYY")
                    with col_d2: del_end = st.date_input("Eliminar Hasta (Inclusivo):", format="DD/MM/YYYY")
                    
                    if st.button("🗑️ Eliminar Rango Completo", type="primary"):
                        count_deleted = 0
                        start_dt = datetime.combine(del_start, datetime.min.time())
                        end_dt = datetime.combine(del_end, datetime.min.time())
                        for r in list(user_reservas): # work on copy
                            if start_dt <= r["date_obj"] <= end_dt:
                                if r["date"] in reservas_db[act_lab] and r["block"] in reservas_db[act_lab][r["date"]]:
                                    target_arr = reservas_db[act_lab][r["date"]][r["block"]]["bookings"]
                                    for k in range(len(target_arr) - 1, -1, -1):
                                        if target_arr[k]["owner_email"] == st.session_state.email and target_arr[k]["display"] == r["display"]:
                                            target_arr.pop(k)
                                            count_deleted += 1
                                            break
                                    if not target_arr:
                                        del reservas_db[act_lab][r["date"]][r["block"]]
                                    if not reservas_db[act_lab][r["date"]]:
                                        del reservas_db[act_lab][r["date"]]
                        
                        if count_deleted > 0:
                            save_reservas(reservas_db)
                            st.session_state.success_msg = f"Se han retirado {count_deleted} inscripciones en el rango."
                            st.rerun()
                        else:
                            st.warning("No tienes reservas en ese rango.")
                            
                with tab3:
                    st.info("Elimina masivamente reservas de un mes particular.")
                    meses = {"01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril", "05": "Mayo", "06": "Junio", 
                             "07": "Julio", "08": "Agosto", "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"}
                    col_m1, col_m2 = st.columns(2)
                    with col_m1: selected_month = st.selectbox("Mes", options=list(meses.keys()), format_func=lambda x: meses[x], index=datetime.now().month - 1)
                    with col_m2: selected_year = st.number_input("Año", min_value=2024, max_value=2040, value=datetime.now().year)
                    
                    if st.button("🗑️ Eliminar Mes Completo", type="primary", key="btn_del_mes"):
                        count_deleted = 0
                        for r in list(user_reservas):
                            if r["date_obj"].month == int(selected_month) and r["date_obj"].year == int(selected_year):
                                if r["date"] in reservas_db[act_lab] and r["block"] in reservas_db[act_lab][r["date"]]:
                                    target_arr = reservas_db[act_lab][r["date"]][r["block"]]["bookings"]
                                    for k in range(len(target_arr) - 1, -1, -1):
                                        if target_arr[k]["owner_email"] == st.session_state.email and target_arr[k]["display"] == r["display"]:
                                            target_arr.pop(k)
                                            count_deleted += 1
                                            break
                                    if not target_arr:
                                        del reservas_db[act_lab][r["date"]][r["block"]]
                                    if not reservas_db[act_lab][r["date"]]:
                                        del reservas_db[act_lab][r["date"]]
                        if count_deleted > 0:
                            save_reservas(reservas_db)
                            st.session_state.success_msg = f"Se retiraron {count_deleted} inscripciones de {meses[selected_month]} {selected_year}."
                            st.rerun()
                        else:
                            st.warning("Sin reservas en ese mes.")

        elif modo == "Panel de Administración" and is_admin:
            act_lab = st.session_state.selected_lab
            act_lab_str = "CADI" if act_lab == "CADI" else "Cs. de la Salud"
            st.header(f"👑 Control Maestro: {act_lab_str}")
            admin_action = st.selectbox("Acción Administrativa", ["Eliminar Cualquier Reserva del Sistema", "Ver Usuarios Registrados"])
            
            if admin_action == "Ver Usuarios Registrados":
                for e, d in users_db.items():
                    st.code(f"{d['name']} ({e})")
                    
            elif admin_action == "Eliminar Cualquier Reserva del Sistema":
                all_raw_reservas = []
                unique_emails = set()
                
                for d_str, day_blocks in reservas_db[act_lab].items():
                    for b_time, b_data in day_blocks.items():
                        for bk in b_data.get("bookings", []):
                            em = bk.get("owner_email", "Legado")
                            unique_emails.add(em)
                            all_raw_reservas.append({
                                "date": d_str, 
                                "date_obj": datetime.strptime(d_str, "%Y-%m-%d"),
                                "block": b_time, 
                                "display": bk.get("display", "Sin Nombre"),
                                "email": em
                            })
                        
                if not all_raw_reservas:
                    st.success("El laboratorio está completamente vacío.")
                else:
                    st.write("Filtra por profesor:")
                    user_options = ["Todos los Usuarios"] + sorted(list(unique_emails))
                    selected_target_user = st.selectbox("Seleccionar Docente a Modificar:", user_options)
                    
                    if selected_target_user == "Todos los Usuarios":
                        filtered_reservas = all_raw_reservas
                    else:
                        filtered_reservas = [r for r in all_raw_reservas if r["email"] == selected_target_user]
                        
                    if not filtered_reservas:
                        st.info("Sin reservas.")
                    else:
                        st.write("Opciones de Eliminación:")
                        tab_a1, tab_a2, tab_a3 = st.tabs(["Individual", "Rango", "Mes"])
                        
                        with tab_a1:
                            sorted_filtered = sorted(filtered_reservas, key=lambda x: (x["date"], x["block"]))
                            grouped_admin = {}
                            for r in sorted_filtered:
                                grouped_admin.setdefault(r["date"], []).append(r)
                                
                            for date_key, items in grouped_admin.items():
                                fecha_str = datetime.strptime(date_key, '%Y-%m-%d').strftime('%d/%m/%Y')
                                with st.expander(f"📅 Fecha: {fecha_str}"):
                                    for idx, r in enumerate(items):
                                        col_txt, col_btn = st.columns([3, 1])
                                        with col_txt: st.write(f"**{r['block']}** | {r['email']} | {r['display']}")
                                        with col_btn:
                                            if st.button("Forzar Eliminación", key=f"admin_del_{r['date']}_{r['block']}_{idx}"):
                                                target_arr = reservas_db[act_lab][r["date"]][r["block"]]["bookings"]
                                                for k, entry in enumerate(target_arr):
                                                    if entry["owner_email"] == r["email"] and entry["display"] == r["display"]:
                                                        target_arr.pop(k)
                                                        break
                                                if not target_arr:
                                                    del reservas_db[act_lab][r["date"]][r["block"]]
                                                if not reservas_db[act_lab][r["date"]]:
                                                    del reservas_db[act_lab][r["date"]]
                                                save_reservas(reservas_db)
                                                st.rerun()
                                                
                        with tab_a2:
                            col_d1, col_d2 = st.columns(2)
                            with col_d1: del_start = st.date_input("Desde:", key="admin_d1", format="DD/MM/YYYY")
                            with col_d2: del_end = st.date_input("Hasta:", key="admin_d2", format="DD/MM/YYYY")
                            
                            if st.button("🗑️ Eliminar Rango", type="primary", key="admin_btn_rng"):
                                count_deleted = 0
                                start_dt = datetime.combine(del_start, datetime.min.time())
                                end_dt = datetime.combine(del_end, datetime.min.time())
                                for r in filtered_reservas:
                                    if start_dt <= r["date_obj"] <= end_dt:
                                        if r["date"] in reservas_db[act_lab] and r["block"] in reservas_db[act_lab][r["date"]]:
                                            target_arr = reservas_db[act_lab][r["date"]][r["block"]]["bookings"]
                                            for k in range(len(target_arr) - 1, -1, -1):
                                                if target_arr[k]["owner_email"] == r["email"] and target_arr[k]["display"] == r["display"]:
                                                    target_arr.pop(k)
                                                    count_deleted += 1
                                                    break
                                            if not target_arr:
                                                del reservas_db[act_lab][r["date"]][r["block"]]
                                            if not reservas_db[act_lab][r["date"]]:
                                                del reservas_db[act_lab][r["date"]]
                                if count_deleted > 0:
                                    save_reservas(reservas_db)
                                    st.session_state.success_msg = f"Se forzaron {count_deleted} eliminaciones."
                                    st.rerun()
                                    
                        with tab_a3:
                            meses = {"01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril", "05": "Mayo", "06": "Junio", 
                                     "07": "Julio", "08": "Agosto", "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"}
                            col_m1, col_m2 = st.columns(2)
                            with col_m1: selected_month = st.selectbox("Mes", options=list(meses.keys()), format_func=lambda x: meses[x], index=datetime.now().month - 1, key="admin_m1")
                            with col_m2: selected_year = st.number_input("Año", min_value=2024, max_value=2040, value=datetime.now().year, key="admin_m2")
                            
                            if st.button("🗑️ Eliminar Mes", type="primary", key="admin_btn_mes"):
                                count_deleted = 0
                                for r in filtered_reservas:
                                    if r["date_obj"].month == int(selected_month) and r["date_obj"].year == int(selected_year):
                                        if r["date"] in reservas_db[act_lab] and r["block"] in reservas_db[act_lab][r["date"]]:
                                            target_arr = reservas_db[act_lab][r["date"]][r["block"]]["bookings"]
                                            for k in range(len(target_arr) - 1, -1, -1):
                                                if target_arr[k]["owner_email"] == r["email"] and target_arr[k]["display"] == r["display"]:
                                                    target_arr.pop(k)
                                                    count_deleted += 1
                                                    break
                                            if not target_arr:
                                                del reservas_db[act_lab][r["date"]][r["block"]]
                                            if not reservas_db[act_lab][r["date"]]:
                                                del reservas_db[act_lab][r["date"]]
                                if count_deleted > 0:
                                    save_reservas(reservas_db)
                                    st.session_state.success_msg = f"Se forzaron {count_deleted} eliminaciones."
                                    st.rerun()

    # --- TABLA DE HORARIOS ---
    act_lab = st.session_state.selected_lab
    if act_lab == "CADI":
        st.subheader("📊 Visualizador: Laboratorio de Análisis de Movimiento (CADI)")
    elif act_lab == "FACSA":
        st.subheader("📊 Visualizador: Laboratorio de Kinesiología (Facultad Cs. de la Salud)")
    colA, colB = st.columns([1, 4])
    with colA:
        view_week_start = st.date_input("Ver semana a partir del Lunes:", value=start_of_week, format="DD/MM/YYYY")
        
    view_monday = view_week_start - timedelta(days=view_week_start.weekday())
    week_dates = [(view_monday + timedelta(days=i)) for i in range(7)]
    cols = [f"{days_of_week[d.weekday()]} {d.strftime('%d/%m')}" for d in week_dates]

    df_data = []
    for b in blocks:
        row = {"Bloque Horario": b}
        for i, d in enumerate(week_dates):
            d_str = d.strftime("%Y-%m-%d")
            if d_str in reservas_db[act_lab] and b in reservas_db[act_lab][d_str]:
                b_data = reservas_db[act_lab][d_str][b]
                displays = [bk.get("display", "Ocupado") for bk in b_data.get("bookings", [])]
                text = " + ".join(displays)
                if not b_data.get("shared", False) and text:
                    text += " (Exclusivo)"
                row[cols[i]] = text if text else "Disponible"
            else:
                row[cols[i]] = "Disponible"
        df_data.append(row)

    df = pd.DataFrame(df_data)

    def highlight_cells(val):
        if val == "Disponible":
            return 'background-color: white; color: #16a34a'
        elif val == "Bloque Horario":
            return ''
        else:
            return 'background-color: #1e40af; color: white; border-radius: 4px;'

    st.dataframe(
        df.style.map(highlight_cells, subset=cols),
        use_container_width=True,
        hide_index=True,
        height=450
    )
