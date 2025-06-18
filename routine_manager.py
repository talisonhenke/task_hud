import tkinter as tk
from tkinter import messagebox
import json
import os
from datetime import datetime
import threading
import time
import winsound

TAREFAS_ARQUIVO = "tasks.json"

# ---------- Funções de Leitura e Escrita ----------
def carregar_tarefas():
    if not os.path.exists(TAREFAS_ARQUIVO):
        with open(TAREFAS_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    try:
        with open(TAREFAS_ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Arquivo corrompido → reescreve com lista vazia
        with open(TAREFAS_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

def salvar_tarefas(tarefas):
    with open(TAREFAS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(tarefas, f, indent=2, ensure_ascii=False)

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
    widget.geometry("")  # Ajuste automático ao tamanho mínimo necessário

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
            restante = int(duracao - (time.time() - inicio))
            if restante <= 0:
                if not tarefa_concluida:
                    timer_label.config(text="00:00", bg="white", fg="red")
                    status.config(text="Tempo esgotado", bg="white", fg="red")
                    play_time_expired_sound()
                break
            minutos = restante // 60
            segundos = restante % 60
            timer_label.config(text=f"{minutos:02}:{segundos:02}")

            percentual = restante / duracao
            if percentual <= 0.3 and not alerta_30:
                widget.configure(bg="red")
                titulo.config(bg="red", fg="white")
                status.config(bg="red", fg="white")
                botao_ok.config(bg="white", fg="black")
                timer_label.config(bg="white", fg="black")
                play_time_warning_sound()
                alerta_30 = True

            time.sleep(1)

    threading.Thread(target=atualizar_timer, daemon=True).start()

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
janela.title("Gerenciador de Rotina")

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

janela.mainloop()
