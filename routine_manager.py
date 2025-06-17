import tkinter as tk
from tkinter import messagebox
import json
import os
from datetime import datetime, timedelta
import threading
import time
import winsound

TAREFAS_ARQUIVO = "tasks.json"

# ---------- Funções de Leitura e Escrita ----------
def carregar_tarefas():
    if not os.path.exists(TAREFAS_ARQUIVO):
        with open(TAREFAS_ARQUIVO, "w") as f:
            json.dump([], f)
    with open(TAREFAS_ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_tarefas(tarefas):
    with open(TAREFAS_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(tarefas, f, indent=2, ensure_ascii=False)

# ---------- Sistema de Notificações ----------
def tocar_som():
    winsound.MessageBeep()

def iniciar_widget(tarefa):
    widget = tk.Toplevel()
    widget.title("Tarefa em andamento")
    widget.geometry("300x200+20+20")
    widget.attributes("-topmost", True)
    widget.configure(bg="white")

    titulo = tk.Label(widget, text=tarefa['titulo'], font=("Helvetica", 16, "bold"), bg="white")
    titulo.pack(pady=10)

    status = tk.Label(widget, text="Tarefa em andamento", font=("Helvetica", 14), bg="white")
    status.pack()

    timer_label = tk.Label(widget, text="", font=("Helvetica", 24), bg="white")
    timer_label.pack(pady=10)

    def finalizar_widget():
        status.config(text="Tarefa concluída", bg="green")
        timer_label.config(bg="green")
        titulo.config(bg="green")
        widget.after(5000, widget.destroy)

    botao_ok = tk.Button(widget, text="OK", font=("Helvetica", 12), command=finalizar_widget)
    botao_ok.pack(pady=10)

    duracao = tarefa['duracao'] * 60
    inicio = time.time()
    alerta_30_percent = False

    def atualizar_timer():
        nonlocal duracao, alerta_30_percent
        while duracao > 0:
            restante = int(duracao)
            minutos = restante // 60
            segundos = restante % 60
            timer_label.config(text=f"{minutos:02}:{segundos:02}")

            percentual = duracao / (tarefa['duracao'] * 60)
            if percentual <= 0.3 and not alerta_30_percent:
                tocar_som()
                alerta_30_percent = True

            time.sleep(1)
            duracao -= 1

        timer_label.config(text="00:00", bg="red")
        status.config(text="Tempo esgotado", bg="red")
        titulo.config(bg="red")

    threading.Thread(target=atualizar_timer, daemon=True).start()

def exibir_popup(tarefa):
    popup = tk.Toplevel()
    popup.title("Notificação de Tarefa")
    popup.attributes("-topmost", True)
    popup.attributes("-fullscreen", True)
    popup.configure(bg="white")

    titulo = tk.Label(popup, text=tarefa['titulo'], font=("Helvetica", 36, "bold"), bg="white")
    titulo.pack(pady=100)

    status = tk.Label(popup, text="Clique em OK para iniciar a tarefa", font=("Helvetica", 24), bg="white")
    status.pack()

    def iniciar_tarefa():
        popup.destroy()
        iniciar_widget(tarefa)

    botao_ok = tk.Button(popup, text="OK", font=("Helvetica", 24), command=iniciar_tarefa)
    botao_ok.pack(pady=30)

    tocar_som()

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
