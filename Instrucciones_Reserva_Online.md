# Instalación del Sistema de Reservas de Laboratorio (Google Workspace)

Para automatizar las reservas de manera gratuita, robusta y con tu cuenta institucional, utilizaremos un Formulario de Google enlazado a un Calendario de Google mediante un script que evitará choques de horarios.

Sigue estos 3 simples pasos:

## PASO 1: Crear el Calendario
1. Ve a [Google Calendar](https://calendar.google.com).
2. En el panel izquierdo, haz clic en el botón **+** al lado de "Otros calendarios" y elige **Crear un calendario**.
3. Ponle de nombre **"Reservas Laboratorio Movimiento"** y haz clic en Crear.
4. Una vez creado, ve a la configuración de ese calendario y busca donde dice **"ID de calendario"** (suele verse como una dirección de correo larga, ej. `c_123456@group.calendar.google.com`). Cópiala y guárdala, la necesitaremos en el paso 3.

## PASO 2: Crear el Formulario de Reservas
1. Ve a [Google Forms](https://forms.google.com) y crea un nuevo formulario llamado "Reserva Laboratorio de Análisis de Movimiento".
2. Para que el sistema funcione perfecto, **debes crear exactamente estas 5 preguntas (en este orden)**:
   - **Pregunta 1:** Nombre del Profesor/a (Respuesta Corta - Obligatorio)
   - **Pregunta 2:** Actividad a realizar (Respuesta Corta - Obligatorio)
   - **Pregunta 3:** Fecha de Reserva (Tipo: Fecha - Obligatorio)
   - **Pregunta 4:** Bloque Horario de Inicio (Tipo: Desplegable - Obligatorio)
   - **Pregunta 5:** Bloque Horario de Fin (Tipo: Desplegable - Obligatorio)

   *Nota: En las preguntas de Bloque Horario, agrega como opciones los bloques de 24 hrs que usas (Ej: `08:00`, `09:30`, `11:10`, `12:40`, `14:30`, `16:10`, `17:50`, `19:20`).*

3. Ve a la pestaña **Configuración** del formulario y activa "Recopilar direcciones de correo electrónico".

## PASO 3: Conectar el Formulario al Calendario con Apps Script
1. Estando en tu Formulario de Google, haz click en los **3 puntos (arriba a la derecha)** y selecciona **Editor de secuencias de comandos (Script Editor)**.
2. Se abrirá una pestaña nueva. Borra el código corto que aparece allí y pega el siguiente código en su lugar:

```javascript
// --- CONFIGURACIÓN ---
// REEMPLAZA ESTO CON EL ID DE TU CALENDARIO (Paso 1)
const CALENDAR_ID = 'TU_ID_DE_CALENDARIO_AQUI@group.calendar.google.com'; 
const NOMBRES_COLUMNAS = {
  EMAIL: 'Dirección de correo electrónico',
  NOMBRE: 'Nombre del Profesor/a',
  ACTIVIDAD: 'Actividad a realizar',
  FECHA: 'Fecha de Reserva',
  HORA_INICIO: 'Bloque Horario de Inicio',
  HORA_FIN: 'Bloque Horario de Fin'
};

function onFormSubmit(e) {
  try {
    const respuestas = e.namedValues;
    const email = respuestas[NOMBRES_COLUMNAS.EMAIL] ? respuestas[NOMBRES_COLUMNAS.EMAIL][0] : "Sin correo";
    const nombre = respuestas[NOMBRES_COLUMNAS.NOMBRE][0];
    const actividad = respuestas[NOMBRES_COLUMNAS.ACTIVIDAD][0];
    const fechaString = respuestas[NOMBRES_COLUMNAS.FECHA][0]; // Formato dd/mm/yyyy
    const horaInicioString = respuestas[NOMBRES_COLUMNAS.HORA_INICIO][0]; // Formato hh:mm
    const horaFinString = respuestas[NOMBRES_COLUMNAS.HORA_FIN][0]; // Formato hh:mm
    
    // Parsear Fechas
    const [dia, mes, ano] = fechaString.split('/').map(Number);
    const [hInicio, mInicio] = horaInicioString.split(':').map(Number);
    const [hFin, mFin] = horaFinString.split(':').map(Number);
    
    const fechaInicioEvent = new Date(ano, mes - 1, dia, hInicio, mInicio);
    const fechaFinEvent = new Date(ano, mes - 1, dia, hFin, mFin);
    
    const calendario = CalendarApp.getCalendarById(CALENDAR_ID);
    
    // Validar si el evento termina antes de que empieza por error humano
    if (fechaFinEvent <= fechaInicioEvent) {
      enviarCorreoRechazo(email, nombre, actividad, "La hora de finalización debe ser posterior a la de inicio.");
      return;
    }

    // Comprobar disponibilidad (choque de horario)
    const eventosConflictivos = calendario.getEvents(fechaInicioEvent, fechaFinEvent);
    
    if (eventosConflictivos.length > 0) {
      // Hay tope de horario
      enviarCorreoRechazo(email, nombre, actividad, "El laboratorio ya se encuentra reservado en ese segmento horario.");
    } else {
      // Todo bien, crear el evento
      const tituloEvento = `Reserva Lab: ${nombre} - ${actividad}`;
      const evento = calendario.createEvent(tituloEvento, fechaInicioEvent, fechaFinEvent);
      evento.addGuest(email); // Agrega al profesor al calendario para que le avise
      
      enviarCorreoConfirmacion(email, nombre, actividad, fechaInicioEvent, fechaFinEvent);
    }
    
  } catch (error) {
    console.error("Error al procesar la reserva: " + error.toString());
  }
}

function enviarCorreoConfirmacion(email, nombre, actividad, fechaInicio, fechaFin) {
  const asunto = "✅ Reserva Confirmada: Laboratorio de Movimiento";
  const mensaje = `Hola ${nombre},\n\nTu reserva para el Laboratorio de Movimiento ha sido CONFIRMADA.\n\nActividad: ${actividad}\nFecha: ${fechaInicio.toLocaleDateString('es-CL')}\nHorario: ${fechaInicio.toLocaleTimeString('es-CL')} a ${fechaFin.toLocaleTimeString('es-CL')}\n\nGracias.`;
  
  if(email !== "Sin correo"){
    MailApp.sendEmail(email, asunto, mensaje);
  }
}

function enviarCorreoRechazo(email, nombre, actividad, motivo) {
  const asunto = "❌ Reserva Rechazada: Tope de Horario Lab Movimiento";
  const mensaje = `Hola ${nombre},\n\nLo lamentamos, pero tu solicitud de reserva para "${actividad}" no pudo ser procesada.\n\nMotivo: ${motivo}\n\nPor favor, revisa el calendario de disponibilidad y vuelve a enviar el formulario seleccionando un horario libre.\n\nGracias.`;
  
  if(email !== "Sin correo"){
    MailApp.sendEmail(email, asunto, mensaje);
  }
}
```

3. **Reemplaza la línea 3** (`const CALENDAR_ID = ...`) con el ID del calendario que guardaste en el Paso 1. Guarda el código dándole click al ícono de disquete arriba.
4. Finalmente, para que el código corra solo cada vez que alguien envía un formulario, ve al **Reloj (Desencadenadores / Triggers)** en el menú de la izquierda del script.
   - Presiona **"Añadir desencadenador"** (botón azul abajo).
   - Función que se va a ejecutar: `onFormSubmit`
   - Fuente del evento: `De un formulario`
   - Tipo de evento: `Al enviarse el formulario`
   - Dale a Guardar. Google te pedirá autorizar permisos de acceso a tu correo y calendario, acéptalos.

¡Listo! Ya tienes un sistema de reservas gratuito, automatizado y conectado a correos electrónicos institucionales. Tus profesores entran al formulario, piden hora, y el sistema automáticamente los agenda o les advierte si hay choque de horarios.
