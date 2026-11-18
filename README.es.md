# 🔦 Zelador

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Zelador](guia/assets/banner-es.jpg)](https://inematds.github.io/zelador/guia/es/)

**El agente Zelador te ayuda a mejorar tu sistema todos los días.** Sin él, solo descubres los problemas cuando alguien se queja. Con él, las rutinas de tu máquina se revisan cada madrugada y, por la mañana, te avisa. Si activas la explicación con tu IA, investiga la causa y sugiere cómo solucionarlo. Tú decides y le pides a la IA que lo haga.

## 📖 Guía

Para entender qué hace y cómo puede cambiar tu día (sin tecnicismos): **https://inematds.github.io/zelador/guia/es/**

## Qué es

Quienes dejan robots y agentes de IA trabajando por su cuenta solo descubren los problemas cuando alguien se queja. Zelador es un programa gratuito que se encarga de vigilarlo por ti: cada madrugada revisa qué falló y, cada semana, reúne en un formulario sencillo lo que conviene mejorar para que tú decidas. Si todavía no llevas un registro de fallas y pendientes, crea los archivos. Si ya los llevas, usa los tuyos. Para instalarlo, solo tienes que pedírselo a tu IA.

## Qué ve y qué no ve

- **Ve:** tareas programadas en la propia computadora o servidor Linux que fallan, registran errores o dejan de ejecutarse (el ritmo de cada una se determina según el historial de la máquina), falta de memoria, errores repetidos, disco casi lleno y todo lo que tú o tu IA anotan en las listas de fallas, límites y pendientes.
- **No ve:** lo que se ejecuta en servicios de internet, tareas del sistema, del administrador o de otra cuenta, tareas de cron sin archivo de registro ni resultados incorrectos que no dejen señales (salvo que se anote la falla).
- **Sin nadie conectado** (servidor o computadora que se reinició): las tareas programadas de la cuenta solo se ejecutan con `sudo loginctl enable-linger <usuário>`. El diagnóstico avisa si falta.
- **Si no llega ningún mensaje por la mañana, desconfía:** por defecto, envía una línea incluso cuando la noche transcurrió sin problemas, así que el silencio puede indicar que la revisión no se ejecutó.
- **Datos sensibles:** el aviso y el informe pueden incluir fragmentos de los registros, y la explicación con IA envía el título, la propuesta y las evidencias. Si los registros contienen datos de clientes, usa `noite.trechos = false` y deja `explicar.comando` vacío.
- Las tareas de cron solo se detectan por lo que aparece en el archivo de registro: usa `>> arquivo.log 2>&1`.
- Si no puede revisar alguna parte, el aviso indica cuál, en vez de decir que la noche transcurrió sin problemas.
- El aviso solo se envía después de que eliges el canal. El formulario se abre en la computadora donde está Zelador, y la dirección aparece en cada informe de la madrugada; para abrirlo en el celular, conecta ambos dispositivos a una red privada y agrega la dirección a `painel.enderecos` y `painel.link`.
- Probado en Linux. Mac y Windows todavía no se han probado.

## Cómo empezar (sin ser técnico)

Abre Claude Code o Codex en la máquina donde se ejecutan las rutinas, en la carpeta donde están tus proyectos, y pega esto:

```text
Lee el proyecto Zelador en https://github.com/inematds/zelador (el README explica todo, incluida la instalación).
Descarga una copia en una carpeta temporal, fuera de mis proyectos, y ejecuta solo el diagnóstico desde la carpeta donde están mis proyectos (búscala; si no tengo una, continúa sin ella). No cambies nada.
Después respóndeme en español sencillo:
1. ¿Puede detectar las rutinas que se ejecutan aquí? ¿Qué vería, qué no vería y seguiría ejecutándose sin que nadie esté conectado?
2. ¿Qué tengo ya que pueda aprovechar?
3. ¿Qué falta y crearía?
4. ¿Por qué medios recibiría los avisos y qué tendría que hacer para eso?
Todavía no instales ni cambies nada. Muéstrame el plan y espera a que te diga que sí.
Cuando te diga que sí, instálalo en una carpeta permanente, nunca en la temporal.
```

---

## Instalación técnica

Python 3.11+, solo biblioteca estándar. Probado en Linux; si una fuente no existe en la máquina (sin `journalctl` o sin cron), se omite y aparece como omitida en el informe. Sin API: la explicación con IA es opcional y usa el comando que elijas (por ejemplo, `claude -p` con tu suscripción).

```bash
git clone https://github.com/inematds/zelador.git && cd zelador
python3 -m unittest discover -s tests -v     # 27 testes, sem rede
bin/zelador iniciar                          # diagnóstico: não escreve nada
bin/zelador iniciar --aplicar                # cria o que falta, nunca sobrescreve
bin/zelador bloco                            # instrução para colar no CLAUDE.md/AGENTS.md
bin/zelador agendar --aplicar                # (clone numa pasta permanente) madrugada 04:20, pauta segunda 07:45, painel sempre ligado
```

El diagnóstico responde pieza por pieza:

| Salida | Quiere decir |
|---|---|
| `✓ JÁ TEM` | el zelador lo usa tal como está |
| `→ PROPOSTA` | tienes algo parecido o puedes conectar una fuente; lo explica y tú decides |
| `+ CRIAR` | no existe nada; con `--aplicar` lo crea a partir del modelo |

Un nombre parecido (`ERRORS.md`, `TODO.md`) solo se adopta con `--aplicar` si todavía no tienes ningún archivo de ese tipo. Si ya tienes uno, queda como sugerencia.

## El proceso, de principio a fin

🧠 tú · ⚙️ script/timer · 🤖 IA (opcional)

| # | Paso | Comando | Quién |
|---|---|---|---|
| 1 | Revisar qué tienes y qué falta | `zelador iniciar` | 🧠 |
| 2 | Crear lo que falta y registrar lo que ya usas | `zelador iniciar --aplicar` | ⚙️ |
| 3 | Pedirle al agente que registre fallas, límites y pendientes (pégalo en CLAUDE.md/AGENTS.md) | `zelador bloco` | 🧠 |
| 4 | Elegir cómo recibir los avisos (Telegram, escritorio o ninguno) y, si quieres, la IA que los explica | editar `~/.config/zelador/zelador.toml` | 🧠 |
| 5 | Programar las tareas | `zelador agendar --aplicar` | ⚙️ |
| 6 | Todos los días a las 04:20: fallas de rutinas, falta de memoria, errores repetidos, errores de cron, registros nuevos, disco | `zelador noite` | ⚙️ |
| 7 | Todos los lunes a las 07:45: resumen con las fallas que se repiten, madrugadas con problemas graves, tus otros monitores, límites abiertos y pendientes sin resolver | `zelador pauta --avisar` | ⚙️ |
| 8 | Cada elemento nuevo recibe una explicación sencilla, la causa probable y una posible solución. Lee el final de los registros de la rutina y los logs recientes del proyecto e intenta ocultar contraseñas, sin garantía (`explicar.ler_registros`) | `explicar.comando` | 🤖 |
| 9 | Leer y decidir en el panel: Aprobar, Rechazar (desaparece durante 8 semanas), Analizar, Posponer, con una nota | `zelador painel` → http://127.0.0.1:8810/ | 🧠 |
| 10 | Cerrar la semana: las aprobadas y las que estén en «analizar» se agregan a los pendientes, y el aviso envía el resultado | botón en el panel | 🧠 |

## Dónde está cada cosa

- Configuración: `~/.config/zelador/zelador.toml` (ejemplo comentado en `exemplos/zelador.toml`).
- Datos: `~/.local/share/zelador/` — `noite/` (informes de la madrugada), `pautas/`, `decisoes.json`, `explicacoes.json`.
- Modelos de los archivos que crea: `zelador/modelos/`.
- Aviso por Telegram: `zelador/modelos/avisar-telegram.sh` (el token va en un archivo tuyo, nunca en el repositorio).
- Resumen de demostración, con datos inventados: `exemplos/pauta-demo.json`.

## Seguridad

- El diagnóstico solo lee. `--aplicar` crea archivos que no existen y guarda la configuración anterior en `.toml.antes`.
- Nunca edita tu CLAUDE.md/AGENTS.md: muestra el bloque para que lo pegues.
- El panel escucha solo en `127.0.0.1`; puedes usar otra dirección (VPN) solo si la agregas a `painel.enderecos`.
- `tests/test_sem_dados_sensiveis.py` rechaza rutas del directorio personal, IP, correo electrónico, tokens y configuraciones o datos personales versionados.

## Licencia

MIT.