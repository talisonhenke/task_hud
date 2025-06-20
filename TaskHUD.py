from PIL import Image, ImageDraw
import pystray
import tkinter as tk
from tkinter import messagebox
import json
import sys
import os
from datetime import datetime
import threading
import time
import winsound
import stat
import ctypes
import ctypes.wintypes

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(__file__)

icone_path = os.path.join(base_path, 'icon', 'taskhud.ico')

DOCUMENTOS = os.path.join(os.path.expanduser("~"), "Documents", "TaskHUD")
os.makedirs(DOCUMENTOS, exist_ok=True)
TAREFAS_ARQUIVO = os.path.join(DOCUMENTOS, "tasks.json")

# ---------- Proteção de Arquivo ----------
def proteger_arquivo(caminho):
    # Oculta e protege como leitura
    os.chmod(caminho, stat.S_IREAD)
    ctypes.windll.kernel32.SetFileAttributesW(caminho, 0x02)  # FILE_ATTRIBUTE_HIDDEN

def desbloquear_arquivo(caminho):
    # Remove somente leitura e oculto
    try:
        os.chmod(caminho, stat.S_IWRITE)
        ctypes.windll.kernel32.SetFileAttributesW(caminho, 0x80)  # FILE_ATTRIBUTE_NORMAL
    except Exception as e:
        print("Erro ao desproteger:", e)

# ---------- Ícone do sistema função bandeja ----------
def criar_icone_bandeja(janela):
    from pystray import Icon, MenuItem as item, Menu
    from PIL import Image, ImageDraw
    import threading
    import os

    def mostrar():
        janela.after(0, janela.deiconify)

    def sair():
        icon.stop()
        janela.after(0, janela.destroy)

    try:
        # Caminho fixo, pois os arquivos estão ao lado do executável, na pasta "icon"
        image = Image.open(icone_path)
    except Exception as e:
        print("Erro ao carregar ícone personalizado:", e)
        image = Image.new('RGB', (64, 64), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill="black")

    icon = Icon("TaskHUD", image, "Task HUD", menu=Menu(
        item("Mostrar", mostrar),
        item("Sair", sair)
    ))

    def ao_fechar():
        janela.withdraw()
        if not icon.visible:
            threading.Thread(target=icon.run, daemon=True).start()

    janela.protocol("WM_DELETE_WINDOW", ao_fechar)


# ---------- Funções de Leitura e Escrita ----------
def carregar_tarefas():
    if not os.path.exists(TAREFAS_ARQUIVO):
        with open(TAREFAS_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump([], f)

    desbloquear_arquivo(TAREFAS_ARQUIVO)

    try:
        with open(TAREFAS_ARQUIVO, "r", encoding="utf-8") as f:
            tarefas = json.load(f)
    except json.JSONDecodeError:
        tarefas = []
        with open(TAREFAS_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(tarefas, f)

    proteger_arquivo(TAREFAS_ARQUIVO)
    return tarefas

def salvar_tarefas(tarefas):
    desbloquear_arquivo(TAREFAS_ARQUIVO)

    with open(TAREFAS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(tarefas, f, indent=2, ensure_ascii=False)

    proteger_arquivo(TAREFAS_ARQUIVO)

# ---------- Sistema de Notificações ----------

def play_task_start_sound():
    winsound.PlaySound("audio/start.wav", winsound.SND_FILENAME)

def play_task_end_sound():
    winsound.PlaySound("audio/end.wav", winsound.SND_FILENAME)

def play_time_warning_sound():
    winsound.PlaySound("audio/warning.wav", winsound.SND_FILENAME)

def play_time_expired_sound():
    winsound.PlaySound("audio/expired.wav", winsound.SND_FILENAME)

def iniciar_tarefa(popup, tarefa):
    popup.destroy()
    mostrar_widget_tarefa(tarefa)

def exibir_popup(tarefa):
    popup = tk.Toplevel()
    popup.title("Notificação de Tarefa")
    popup.attributes("-topmost", True)
    popup.attributes("-fullscreen", True)
    popup.configure(bg="white")

    titulo = tk.Label(popup, text=tarefa['titulo'], font=("Helvetica", 36, "bold"), bg="white")
    titulo.pack(pady=30)

    horario_label = tk.Label(popup, text=f"Horário programado: {tarefa['horario']}", font=("Helvetica", 24), bg="white")
    horario_label.pack(pady=10)

    botao_ok = tk.Button(popup, text="Iniciar tarefa", font=("Helvetica", 20), command=lambda: iniciar_tarefa(popup, tarefa))
    botao_ok.pack(pady=20)

    play_task_start_sound()

# ---------- Ícone na barra de tarefas muda com ping----------
def flash_janela(widget):
    hwnd = ctypes.windll.user32.GetParent(widget.winfo_id())
    FLASHW_ALL = 3
    FLASHW_TIMERNOFG = 12

    class FLASHWINFO(ctypes.Structure):
        _fields_ = [('cbSize', ctypes.wintypes.UINT),
                    ('hwnd', ctypes.wintypes.HWND),
                    ('dwFlags', ctypes.wintypes.DWORD),
                    ('uCount', ctypes.wintypes.UINT),
                    ('dwTimeout', ctypes.wintypes.DWORD)]

    flash = FLASHWINFO(ctypes.sizeof(FLASHWINFO), hwnd, FLASHW_ALL, 5, 0)
    ctypes.windll.user32.FlashWindowEx(ctypes.byref(flash))

# ---------- Widget de Tarefa Minimizado ----------
def mostrar_widget_tarefa(tarefa):
    widget = tk.Toplevel()
    widget.title("Tarefa em andamento")
    widget.geometry("300x150+10+10")
    widget.attributes("-topmost", True)

    titulo = tk.Label(widget, text=tarefa['titulo'], font=("Helvetica", 14))
    titulo.pack(pady=5)

    status = tk.Label(widget, text="Tarefa em andamento", font=("Helvetica", 12))
    status.pack()

    timer_label = tk.Label(widget, text="", font=("Helvetica", 24), bg="white", fg="black")
    timer_label.pack(pady=10)

    botao_ok = tk.Button(widget, text="Finalizar tarefa", font=("Segoe UI", 14, "bold"), bg="#000", fg="#fff", command=lambda: concluir_tarefa())
    botao_ok.pack(pady=10, padx=15)

    widget.update_idletasks()
    widget.geometry("")  # Ajuste automático

    duracao = tarefa['duracao'] * 60
    inicio = time.time()
    tarefa_concluida = False
    alerta_30 = False

    def concluir_tarefa():
        nonlocal tarefa_concluida
        tarefa_concluida = True
        status.config(text="Tarefa concluída", bg="white", fg="green")
        play_task_end_sound()
        timer_label.config(fg="green")
        widget.after(5000, widget.destroy)

    def atualizar_timer():
        nonlocal alerta_30
        while True:
            if not widget.winfo_exists():
                break  # Para a thread se a janela for destruída

            restante = int(duracao - (time.time() - inicio))
            if restante <= 0:
                if not tarefa_concluida:
                    if widget.winfo_exists():
                        try:
                            timer_label.config(text="00:00", bg="white", fg="red")
                            status.config(text="Tempo esgotado", bg="white", fg="red")
                            play_time_expired_sound()
                        except tk.TclError:
                            break
                break

            minutos = restante // 60
            segundos = restante % 60

            try:
                timer_label.config(text=f"{minutos:02}:{segundos:02}")
            except tk.TclError:
                break

            percentual = restante / duracao
            if percentual <= 0.3 and not alerta_30:
                if widget.winfo_exists():
                    try:
                        widget.configure(bg="red")
                        titulo.config(bg="red", fg="white")
                        status.config(bg="red", fg="white")
                        botao_ok.config(bg="white", fg="black")
                        timer_label.config(bg="white", fg="black")
                        play_time_warning_sound()
                    except tk.TclError:
                        break
                alerta_30 = True

            time.sleep(1)

    def lembrete_sonoro_minimizado():
        while not tarefa_concluida:
            if widget.state() == 'iconic':  # Minimizado
                winsound.PlaySound("audio/ping.wav", winsound.SND_FILENAME)
                flash_janela(widget)
            time.sleep(60)

    # Intercepta o botão X do widget para apenas minimizar
    def ao_fechar_widget():
        widget.iconify()

    widget.protocol("WM_DELETE_WINDOW", ao_fechar_widget)

    threading.Thread(target=atualizar_timer, daemon=True).start()
    threading.Thread(target=lembrete_sonoro_minimizado, daemon=True).start()

# ---------- Verificação e Disparo de Tarefas ----------
def verificar_tarefas():
    while True:
        agora = datetime.now().strftime("%H:%M")
        tarefas = carregar_tarefas()
        for tarefa in tarefas:
            if tarefa['horario'] == agora:
                threading.Thread(target=exibir_popup, args=(tarefa,), daemon=True).start()
        time.sleep(60)

# ---------- Interface Principal ----------
def atualizar_lista():
    lista.delete(0, tk.END)
    for idx, tarefa in enumerate(carregar_tarefas()):
        lista.insert(tk.END, f"{idx + 1}. {tarefa['titulo']} às {tarefa['horario']} ({tarefa['duracao']} min)")

def adicionar_tarefa():
    titulo = entrada_titulo.get()
    horario = entrada_horario.get()
    duracao = entrada_duracao.get()
    if not titulo or not horario or not duracao:
        messagebox.showwarning("Campos obrigatórios", "Preencha todos os campos.")
        return
    tarefas = carregar_tarefas()
    tarefas.append({"titulo": titulo, "horario": horario, "duracao": int(duracao)})
    salvar_tarefas(tarefas)
    atualizar_lista()
    entrada_titulo.delete(0, tk.END)
    entrada_horario.delete(0, tk.END)
    entrada_duracao.delete(0, tk.END)

def excluir_tarefa():
    sel = lista.curselection()
    if not sel:
        return
    idx = sel[0]
    tarefas = carregar_tarefas()
    tarefas.pop(idx)
    salvar_tarefas(tarefas)
    atualizar_lista()

def editar_tarefa():
    sel = lista.curselection()
    if not sel:
        return
    idx = sel[0]
    tarefas = carregar_tarefas()
    tarefa = tarefas[idx]

    def salvar_edicao():
        nova_tarefa = {
            "titulo": titulo_var.get(),
            "horario": horario_var.get(),
            "duracao": int(duracao_var.get())
        }
        tarefas[idx] = nova_tarefa
        salvar_tarefas(tarefas)
        atualizar_lista()
        janela_edicao.destroy()

    def cancelar_edicao():
        janela_edicao.destroy()

    janela_edicao = tk.Toplevel(janela)
    janela_edicao.title("Editar Tarefa")

    titulo_var = tk.StringVar(value=tarefa['titulo'])
    horario_var = tk.StringVar(value=tarefa['horario'])
    duracao_var = tk.StringVar(value=str(tarefa['duracao']))

    tk.Label(janela_edicao, text="Título").pack()
    tk.Entry(janela_edicao, textvariable=titulo_var).pack()

    tk.Label(janela_edicao, text="Horário (HH:MM)").pack()
    tk.Entry(janela_edicao, textvariable=horario_var).pack()

    tk.Label(janela_edicao, text="Duração (min)").pack()
    tk.Entry(janela_edicao, textvariable=duracao_var).pack()

    tk.Button(janela_edicao, text="Salvar", command=salvar_edicao).pack(pady=5)
    tk.Button(janela_edicao, text="Voltar", command=cancelar_edicao).pack(pady=5)

# ---------- Iniciar Interface e Threads ----------
janela = tk.Tk()
janela.title("TaskHUD (By Talison Henke)")
janela.iconbitmap(icone_path)

tk.Label(janela, text="Título da tarefa").pack()
entrada_titulo = tk.Entry(janela)
entrada_titulo.pack()

tk.Label(janela, text="Horário (HH:MM)").pack()
entrada_horario = tk.Entry(janela)
entrada_horario.pack()

tk.Label(janela, text="Duração (min)").pack()
entrada_duracao = tk.Entry(janela)
entrada_duracao.pack()

tk.Button(janela, text="Adicionar tarefa", command=adicionar_tarefa).pack(pady=5)
tk.Button(janela, text="Editar tarefa", command=editar_tarefa).pack(pady=5)
tk.Button(janela, text="Excluir tarefa", command=excluir_tarefa).pack(pady=5)

lista = tk.Listbox(janela, width=60)
lista.pack(pady=10)

atualizar_lista()

threading.Thread(target=verificar_tarefas, daemon=True).start()

criar_icone_bandeja(janela)
janela.mainloop()
