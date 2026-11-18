# 🔦 Zelador

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Zelador](guia/assets/banner-es.jpg)](https://inematds.github.io/zelador/guia/es/)

**El agente Zelador te ayuda a mejorar tu sistema todos los días.** Mientras duermes, revisa qué falló. Por la mañana, te avisa. Aprende de lo que se repite. Con tu IA activada, investiga la causa y sugiere una solución. Tú solo decides.

## 📖 Guía

Para entender qué hace y cómo puede cambiar tu día (sin tecnicismos): **https://inematds.github.io/zelador/guia/es/**

## Qué es

Quienes dejan robots y agentes de IA trabajando por su cuenta solo descubren los problemas cuando alguien se queja. Zelador es un programa gratuito que vigila eso por ti: cada madrugada revisa qué falló y cada semana reúne en un formulario sencillo lo que vale la pena mejorar, para que tú decidas. Si todavía no registras fallas ni tareas pendientes, crea los archivos. Si ya lo haces, usa los tuyos. Para instalarlo, basta con pedírselo a tu IA.

## Qué ve y qué no ve

- **Ve:** tareas programadas en la propia computadora o servidor Linux que fallan, registran errores o dejan de ejecutarse (la frecuencia de cada una se calcula a partir del historial de la máquina); falta de memoria, errores repetidos, disco casi lleno y todo lo que tú o tu IA registran en las listas de fallas, límites y tareas pendientes.
- **No ve:** lo que se ejecuta en servicios de internet, tareas del sistema, del administrador o de otra cuenta, tareas de cron sin archivo de registro ni resultados incorrectos que no dejan rastro (a menos que la falla quede registrada).
- **Sin nadie conectado** (servidor o computadora que se reinició): las tareas programadas de la cuenta solo se ejecutan con `sudo loginctl enable-linger <usuário>`. El diagnóstico avisa si falta.
- **Si no recibes ningún mensaje por la mañana, desconfía:** por defecto, envía una línea incluso cuando la noche estuvo tranquila, así que el silencio indica que la ronda quizá no se ejecutó.
- **Datos sensibles:** el aviso y el informe pueden incluir fragmentos de los registros, y la explicación con IA envía el título, la propuesta y las evidencias. Si los registros contienen datos de clientes, usa `noite.trechos = false` y deja `explicar.comando` vacío.
- Las tareas de cron solo se detectan por lo que aparece en el archivo de registro: usa `>> arquivo.log 2>&1`.
- Si no puede revisar alguna parte, el aviso indica cuál, en vez de decir que la noche estuvo tranquila.
- El aviso solo se envía después de que eliges el canal. El formulario se abre en la computadora donde está Zelador, y la dirección aparece en todos los informes de la madrugada; para abrirlo en el celular, conecta ambos dispositivos a una red privada y agrega la dirección en `painel.enderecos` y `painel.link`.
- Probado en Linux. Mac y Windows todavía no se han probado.

## Cómo empezar (sin conocimientos técnicos)

Abre Claude Code o Codex en la máquina donde se ejecutan las tareas, dentro de la carpeta donde están tus proyectos, y pega:

```text
Leia o projeto Zelador em https://github.com/inematds/zelador (o README explica tudo, inclusive a instalação).
Baixe uma cópia numa pasta temporária, fora dos meus projetos, e rode só o diagnóstico, a partir da pasta onde ficam os meus projetos (procure, se eu não souber). Não altere nada.
Depois me responda em espanhol latinoamericano:
1. Ele enxerga as rotinas que rodam aqui? O que ele veria, o que não veria, e ele continua rodando sem ninguém conectado?
2. O que eu já tenho e ele pode aproveitar?
3. O que falta e ele criaria?
4. Por onde eu receberia os avisos, e o que eu precisaria fazer para isso?
Não instale nem mude nada ainda. Mostre o plano e espere eu dizer sim.
Quando eu disser sim, instale numa pasta permanente, nunca na temporária.
```

---

## Instalación técnica

Python 3.11+, solo biblioteca estándar. Probado en Linux; las fuentes que no existen en la máquina (sin `journalctl`, sin cron) se omiten y aparecen como omitidas en el informe. Sin API: la explicación con IA es opcional y usa el comando que elijas (por ejemplo `claude -p` con tu suscripción).

```bash
git clone https://github.com/inematds/zelador.git && cd zelador
python3 -m unittest discover -s tests -v     # 25 testes, sem rede
bin/zelador iniciar                          # diagnóstico: não escreve nada
bin/zelador iniciar --aplicar                # cria o que falta, nunca sobrescreve
bin/zelador bloco                            # instrução para colar no CLAUDE.md/AGENTS.md
bin/zelador agendar --aplicar                # (clone numa pasta permanente) madrugada 04:20, pauta segunda 07:45, painel sempre ligado
```

El diagnóstico responde elemento por elemento:

| Salida | Significado |
|---|---|
| `✓ JÁ TEM` | Zelador lo usa tal como está |
| `→ PROPOSTA` | Tienes algo parecido o puedes activar una fuente; te lo explica para que decidas |
| `+ CRIAR` | No existe nada; con `--aplicar` lo crea a partir de la plantilla |

Un nombre parecido (`ERRORS.md`, `TODO.md`) solo se adopta con `--aplicar` cuando todavía no tienes ningún archivo de ese tipo. Si ya tienes uno, queda como sugerencia.

## El proceso, de principio a fin

🧠 tú · ⚙️ script/timer · 🤖 IA (opcional)

| # | Paso | Comando | Quién |
|---|---|---|---|
| 1 | Revisar lo que ya tienes y lo que falta | `zelador iniciar` | 🧠 |
| 2 | Crear lo que falta y mapear lo que ya usas | `zelador iniciar --aplicar` | ⚙️ |
| 3 | Indicarle al agente que registre fallas, límites y tareas pendientes (pega el bloque en CLAUDE.md/AGENTS.md) | `zelador bloco` | 🧠 |
| 4 | Elegir cómo recibir los avisos (Telegram, escritorio o ninguno) y, si quieres, qué IA los explica | editar `~/.config/zelador/zelador.toml` | 🧠 |
| 5 | Programar las tareas | `zelador agendar --aplicar` | ⚙️ |
| 6 | Todos los días a las 04:20: fallas en tareas rutinarias, falta de memoria, errores repetidos, errores de cron, registros nuevos y disco | `zelador noite` | ⚙️ |
| 7 | Cada lunes a las 07:45: agenda con las fallas recurrentes, noches graves, tus otros monitores, límites abiertos y tareas pendientes sin movimiento | `zelador pauta --avisar` | ⚙️ |
| 8 | Cada elemento nuevo recibe una explicación sencilla, la causa probable y una solución sugerida. Para ello, lee el final de los registros de la tarea y los logs recientes del proyecto, con las contraseñas ocultas (`explicar.ler_registros`) | `explicar.comando` | 🤖 |
| 9 | Leer y decidir en el panel: Aprobar, Rechazar (desaparece por 8 semanas), Analizar, Posponer, con una nota | `zelador painel` → http://127.0.0.1:8810/ | 🧠 |
| 10 | Cerrar la semana: los elementos aprobados y «analizar» se agregan a las tareas pendientes, y el aviso informa el resultado | botón no painel | 🧠 |

## Dónde está cada cosa

- Configuración: `~/.config/zelador/zelador.toml` (ejemplo comentado en `exemplos/zelador.toml`).
- Datos: `~/.local/share/zelador/` — `noite/` (informes de la madrugada), `pautas/`, `decisoes.json`, `explicacoes.json`.
- Plantillas de los archivos que crea: `zelador/modelos/`.
- Aviso por Telegram: `zelador/modelos/avisar-telegram.sh` (el token va en un archivo tuyo, nunca en el repositorio).
- Agenda de demostración con datos inventados: `exemplos/pauta-demo.json`.

## Seguridad

- El diagnóstico solo lee. `--aplicar` crea archivos que no existen y guarda la configuración anterior en `.toml.antes`.
- Nunca edita tu CLAUDE.md/AGENTS.md: te muestra el bloque para que lo pegues.
- El panel solo escucha en `127.0.0.1`; solo aceptará otra dirección (VPN) si la agregas en `painel.enderecos`.
- `tests/test_sem_dados_sensiveis.py` rechaza que se versionen rutas personales, IP, correo electrónico, tokens, configuraciones o datos personales.

## Licencia

MIT.