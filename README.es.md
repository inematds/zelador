# 🔦 Zelador

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Zelador](guia/assets/banner-es.jpg)](https://inematds.github.io/zelador/guia/es/)

**El agente Zelador te ayuda a mejorar tu sistema todos los días.** Mientras duermes, revisa qué falló. Por la mañana, te avisa. Aprende de lo que se repite y te sugiere cómo corregirlo. Tú solo decides.

## 📖 Guía

Para entender qué hace y cómo cambia tu día (sin detalles técnicos): **https://inematds.github.io/zelador/guia/es/**

## Qué es

Quienes dejan robots y agentes de IA trabajando solos solo descubren los problemas cuando alguien se queja. Zelador es un programa gratuito que vigila esto por ti: cada madrugada comprueba qué falló y, cada semana, reúne en un formulario sencillo lo que vale la pena mejorar para que tú decidas. Si todavía no registras fallas y tareas pendientes, crea los archivos. Si ya las registras, usa los tuyos. Para instalarlo, basta con pedírselo a tu IA.

## Qué ve y qué no ve

- **Ve:** tareas programadas en la propia computadora o en un servidor Linux que fallan, registran errores o dejan de ejecutarse (aprende el ritmo de cada una en unos días); falta de memoria, errores repetidos, disco casi lleno y todo lo que tú o tu IA registren en las listas de fallas, límites y tareas pendientes.
- **No ve:** lo que se ejecuta en servicios de internet, tareas del sistema, del administrador o de otra cuenta, tareas de cron sin archivo de registro ni resultados incorrectos que no dejan señales (a menos que registres la falla).
- **Sin nadie conectado** (servidor o computadora que se reinició): las tareas programadas de la cuenta solo se ejecutan con `sudo loginctl enable-linger <usuário>`. El diagnóstico avisa si falta configurarlo.
- **Si no recibes ningún mensaje por la mañana, desconfía:** por defecto envía una línea incluso en una noche sin problemas, así que el silencio puede indicar que la ronda no se ejecutó.
- **Datos sensibles:** el aviso y el informe pueden incluir fragmentos de los registros, y la explicación con IA envía el título, la propuesta y las evidencias. Si los registros contienen datos de clientes, usa `noite.trechos = false` y deja `explicar.comando` vacío.
- Las tareas de cron solo se detectan por lo que aparece en el archivo de registro: usa `>> arquivo.log 2>&1`.
- Si no puede revisar alguna parte, el aviso indica cuál, en vez de decir que la noche estuvo tranquila.
- El aviso solo se envía después de que eliges el canal. El formulario se abre en la computadora donde está Zelador; para abrirlo en el celular, conecta ambos dispositivos a una red privada e indica la dirección en `painel.enderecos` y `painel.link`.
- Probado en Linux. Mac y Windows todavía no se han probado.

## Cómo empezar (sin conocimientos técnicos)

Abre Claude Code o Codex en la máquina donde se ejecutan las tareas, dentro de la carpeta donde están tus proyectos, y pega esto:

```text
Lee el proyecto Zelador en https://github.com/inematds/zelador (el README lo explica todo, incluida la instalación).
Descarga una copia en una carpeta temporal, fuera de mis proyectos, y ejecuta solo el diagnóstico desde la carpeta donde están mis proyectos (búscala si no lo sé). No cambies nada.
Después, respóndeme en español sencillo:
1. ¿Puede detectar las tareas que se ejecutan aquí? ¿Qué vería, qué no vería y seguiría funcionando sin que nadie esté conectado?
2. ¿Qué tengo ya que pueda aprovechar?
3. ¿Qué falta y crearía?
4. ¿Por dónde recibiría los avisos y qué tendría que hacer para eso?
Todavía no instales ni cambies nada. Muéstrame el plan y espera a que te diga que sí.
Cuando te diga que sí, instálalo en una carpeta permanente, nunca en la temporal.
```

---

## Instalación técnica

Python 3.11+, solo biblioteca estándar. Probado en Linux; si alguna fuente no existe en la máquina (sin `journalctl`, sin cron), se omite y aparece como omitida en el informe. Sin API: la explicación con IA es opcional y usa el comando que elijas (por ejemplo `claude -p` con la suscripción).

```bash
git clone https://github.com/inematds/zelador.git && cd zelador
python3 -m unittest discover -s tests -v     # 23 testes, sem rede
bin/zelador iniciar                          # diagnóstico: no escribe nada
bin/zelador iniciar --aplicar                # crea lo que falta, nunca sobrescribe
bin/zelador bloco                            # instrucción para pegar en CLAUDE.md/AGENTS.md
bin/zelador agendar --aplicar                # (clone numa pasta permanente) madrugada 04:20, pauta segunda 07:45, painel sempre ligado
```

El diagnóstico responde elemento por elemento:

| Salida | Significado |
|---|---|
| `✓ JÁ TEM` | Zelador lo usa tal como está |
| `→ PROPOSTA` | tienes algo parecido o puedes conectar una fuente; te lo explica y tú decides |
| `+ CRIAR` | no existe; con `--aplicar` lo crea a partir del modelo |

Un nombre parecido (`ERRORS.md`, `TODO.md`) solo se adopta con `--aplicar` cuando todavía no tienes ningún archivo de ese tipo. Si ya tienes uno, queda como sugerencia.

## El proceso, de principio a fin

🧠 tú · ⚙️ script/timer · 🤖 IA (opcional)

| # | Paso | Comando | Quién |
|---|---|---|---|
| 1 | Ver qué tienes y qué falta | `zelador iniciar` | 🧠 |
| 2 | Crear lo que falta y mapear lo que ya usas | `zelador iniciar --aplicar` | ⚙️ |
| 3 | Indicarle al agente que registre fallas, límites y tareas pendientes (pega el bloque en CLAUDE.md/AGENTS.md) | `zelador bloco` | 🧠 |
| 4 | Elegir el aviso (Telegram, escritorio o ninguno) y, si quieres, la IA que explica | editar `~/.config/zelador/zelador.toml` | 🧠 |
| 5 | Programar las tareas | `zelador agendar --aplicar` | ⚙️ |
| 6 | Todos los días a las 04:20: fallas de tareas, falta de memoria, errores repetidos, errores de cron, nuevos registros, disco | `zelador noite` | ⚙️ |
| 7 | Todos los lunes a las 07:45: agenda con las fallas recurrentes, noches graves, otros monitores, límites abiertos y tareas pendientes estancadas | `zelador pauta --avisar` | ⚙️ |
| 8 | Cada elemento nuevo recibe una explicación sencilla: qué pasó, por qué importa y qué hace la propuesta | `explicar.comando` | 🤖 |
| 9 | Leer y decidir en el panel: Aprobar, Rechazar (desaparece por 8 semanas), Analizar, Posponer, con una nota | `zelador painel` → http://127.0.0.1:8810/ | 🧠 |
| 10 | Cerrar la semana: lo aprobado y lo marcado como «analizar» se agrega a las tareas pendientes, y el aviso envía el resumen | botón en el panel | 🧠 |

## Dónde está cada cosa

- Configuración: `~/.config/zelador/zelador.toml` (ejemplo comentado en `exemplos/zelador.toml`).
- Datos: `~/.local/share/zelador/` — `noite/` (informes de madrugada), `pautas/`, `decisoes.json`, `explicacoes.json`.
- Modelos de los archivos que crea: `zelador/modelos/`.
- Aviso por Telegram: `zelador/modelos/avisar-telegram.sh` (token en un archivo tuyo, nunca en el repositorio).
- Agenda de demostración, con datos inventados: `exemplos/pauta-demo.json`.

## Seguridad

- El diagnóstico solo lee. `--aplicar` crea archivos que no existen y guarda la configuración anterior en `.toml.antes`.
- Nunca edita tu CLAUDE.md/AGENTS.md: te muestra el bloque para que lo pegues.
- El panel escucha solo en `127.0.0.1`; se habilita otra dirección (VPN) solo si la agregas en `painel.enderecos`.
- `tests/test_sem_dados_sensiveis.py` rechaza rutas personales, IP, correo electrónico, tokens y configuraciones o datos personales versionados.

## Licencia

MIT.