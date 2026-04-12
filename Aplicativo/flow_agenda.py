# flow_agenda_completo.py
import sys
import json
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QMessageBox, QStackedWidget,
    QSlider, QComboBox, QLineEdit, QTimeEdit, QSpinBox, QListWidget,
    QListWidgetItem, QDialog, QDialogButtonBox, QFormLayout, QCheckBox,
    QTextEdit, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QTime
from PyQt6.QtGui import QFont, QColor, QPalette, QBrush, QLinearGradient, QIcon


# ==================== MODELO DE DADOS ====================

class Tarefa:
    def __init__(self, nome, horario, duracao_minutos, cor, subtarefas=None, nivel_barulho="🌿 Silencioso",
                 descricao=""):
        self.nome = nome
        self.horario = horario  # string "HH:MM"
        self.duracao_minutos = duracao_minutos
        self.cor = cor  # azul, verde, amarelo, vermelho, roxo
        self.subtarefas = subtarefas if subtarefas else []
        self.nivel_barulho = nivel_barulho
        self.descricao = descricao
        self.concluida = False
        self.em_andamento = False
        self.id = id(self)  # Identificador único

    def to_dict(self):
        return {
            "nome": self.nome,
            "horario": self.horario,
            "duracao_minutos": self.duracao_minutos,
            "cor": self.cor,
            "subtarefas": self.subtarefas,
            "nivel_barulho": self.nivel_barulho,
            "descricao": self.descricao,
            "concluida": self.concluida
        }

    @staticmethod
    def from_dict(data):
        t = Tarefa(
            data["nome"], data["horario"], data["duracao_minutos"],
            data["cor"], data.get("subtarefas", []),
            data.get("nivel_barulho", "🌿 Silencioso"),
            data.get("descricao", "")
        )
        t.concluida = data.get("concluida", False)
        return t


# ==================== CORES E ESTILOS ====================

CORES_TEMA = {
    "azul": {"nome": "🔵 Tarefa sozinho", "hex": "#4A90D9", "rgb": (74, 144, 217)},
    "verde": {"nome": "🟢 Tarefa prazerosa", "hex": "#50C878", "rgb": (80, 200, 120)},
    "amarelo": {"nome": "🟡 Transição", "hex": "#FFD700", "rgb": (255, 215, 0)},
    "vermelho": {"nome": "🔴 Obrigação social", "hex": "#E74C3C", "rgb": (231, 76, 60)},
    "roxo": {"nome": "🟣 Surpresa", "hex": "#9B59B6", "rgb": (155, 89, 182)}
}

NIVEIS_BARULHO = ["🌿 Silencioso", "📢 Moderado", "⚠️ Caótico"]

PERFIS_ENERGIA = {
    "Baixa Energia (Overload)": {
        "bg_color": "#2C2C2C",
        "text_color": "#E0E0E0",
        "card_opacity": 0.85,
        "animacoes": False,
        "aviso_vibracao": True
    },
    "Normal": {
        "bg_color": "#1E1E2E",
        "text_color": "#CDD6F4",
        "card_opacity": 1.0,
        "animacoes": True,
        "aviso_vibracao": True
    },
    "Hiperfoco": {
        "bg_color": "#000000",
        "text_color": "#FFFFFF",
        "card_opacity": 1.0,
        "animacoes": False,
        "aviso_vibracao": False
    }
}


# ==================== DIÁLOGO DE EDIÇÃO DE TAREFAS ====================

class DialogoTarefa(QDialog):
    """Diálogo para criar/editar tarefas com interface acessível"""

    def __init__(self, tarefa=None, parent=None):
        super().__init__(parent)
        self.tarefa = tarefa
        self.setup_ui()

        if tarefa:
            self.carregar_dados_tarefa()
            self.setWindowTitle("✏️ Editar Tarefa")
        else:
            self.setWindowTitle("➕ Nova Tarefa")

    def setup_ui(self):
        self.setMinimumSize(500, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E2E;
            }
            QLabel {
                color: #CDD6F4;
                font-size: 13px;
            }
            QLineEdit, QTimeEdit, QSpinBox, QComboBox, QTextEdit {
                background-color: #313244;
                color: #CDD6F4;
                border: 1px solid #45475A;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus, QTimeEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
                border: 2px solid #89B4FA;
            }
            QGroupBox {
                color: #CDD6F4;
                border: 2px solid #45475A;
                border-radius: 8px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #89B4FA;
                color: #1E1E2E;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B4BEFE;
            }
            QPushButton[color="red"] {
                background-color: #F38BA8;
            }
            QPushButton[color="red"]:hover {
                background-color: #F9E2AF;
            }
        """)

        layout = QVBoxLayout(self)

        # Formulário principal
        form_layout = QFormLayout()

        # Nome da tarefa
        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Ex: Reunião com equipe, Estudar matemática...")
        form_layout.addRow("📝 Nome da tarefa:*", self.nome_input)

        # Horário
        self.horario_input = QTimeEdit()
        self.horario_input.setDisplayFormat("HH:mm")
        self.horario_input.setTime(QTime.currentTime())
        form_layout.addRow("⏰ Horário:*", self.horario_input)

        # Duração
        self.duracao_input = QSpinBox()
        self.duracao_input.setRange(5, 480)  # 5 min a 8 horas
        self.duracao_input.setSuffix(" minutos")
        self.duracao_input.setValue(30)
        form_layout.addRow("⏱️ Duração:*", self.duracao_input)

        # Cor/Tipo
        self.cor_input = QComboBox()
        for key, value in CORES_TEMA.items():
            self.cor_input.addItem(value["nome"], key)
        form_layout.addRow("🎨 Tipo de atividade:", self.cor_input)

        # Nível de barulho
        self.barulho_input = QComboBox()
        self.barulho_input.addItems(NIVEIS_BARULHO)
        form_layout.addRow("🔊 Nível de barulho:", self.barulho_input)

        layout.addLayout(form_layout)

        # Grupo de subtarefas
        self.subtarefas_group = QGroupBox("🚂 Modo Trem - Etapas da tarefa")
        subtarefas_layout = QVBoxLayout()

        self.lista_subtarefas = QListWidget()
        self.lista_subtarefas.setMaximumHeight(150)
        subtarefas_layout.addWidget(self.lista_subtarefas)

        # Botões para gerenciar subtarefas
        botoes_sub = QHBoxLayout()
        self.btn_add_sub = QPushButton("➕ Adicionar etapa")
        self.btn_add_sub.clicked.connect(self.adicionar_subtarefa)
        self.btn_remove_sub = QPushButton("❌ Remover etapa")
        self.btn_remove_sub.clicked.connect(self.remover_subtarefa)
        self.btn_edit_sub = QPushButton("✏️ Editar etapa")
        self.btn_edit_sub.clicked.connect(self.editar_subtarefa)

        botoes_sub.addWidget(self.btn_add_sub)
        botoes_sub.addWidget(self.btn_edit_sub)
        botoes_sub.addWidget(self.btn_remove_sub)
        subtarefas_layout.addLayout(botoes_sub)

        self.subtarefas_group.setLayout(subtarefas_layout)
        layout.addWidget(self.subtarefas_group)

        # Descrição detalhada
        self.descricao_input = QTextEdit()
        self.descricao_input.setPlaceholderText("Descrição detalhada da tarefa, materiais necessários, dicas...")
        self.descricao_input.setMaximumHeight(100)
        layout.addWidget(QLabel("📋 Descrição detalhada (opcional):"))
        layout.addWidget(self.descricao_input)

        # Botões OK/Cancelar
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

    def adicionar_subtarefa(self):
        texto, ok = QInputDialog.getText(self, "Nova etapa", "Digite o passo a passo:")
        if ok and texto.strip():
            self.lista_subtarefas.addItem(texto.strip())

    def remover_subtarefa(self):
        item_atual = self.lista_subtarefas.currentItem()
        if item_atual:
            row = self.lista_subtarefas.row(item_atual)
            self.lista_subtarefas.takeItem(row)

    def editar_subtarefa(self):
        item_atual = self.lista_subtarefas.currentItem()
        if item_atual:
            texto, ok = QInputDialog.getText(self, "Editar etapa", "Modificar passo:", text=item_atual.text())
            if ok and texto.strip():
                item_atual.setText(texto.strip())

    def carregar_dados_tarefa(self):
        """Carrega dados da tarefa existente no formulário"""
        self.nome_input.setText(self.tarefa.nome)

        # Horário
        hora, minuto = map(int, self.tarefa.horario.split(":"))
        self.horario_input.setTime(QTime(hora, minuto))

        self.duracao_input.setValue(self.tarefa.duracao_minutos)

        # Cor
        index = self.cor_input.findData(self.tarefa.cor)
        if index >= 0:
            self.cor_input.setCurrentIndex(index)

        # Barulho
        if self.tarefa.nivel_barulho in NIVEIS_BARULHO:
            self.barulho_input.setCurrentText(self.tarefa.nivel_barulho)

        # Subtarefas
        for sub in self.tarefa.subtarefas:
            self.lista_subtarefas.addItem(sub)

        # Descrição
        self.descricao_input.setPlainText(self.tarefa.descricao)

    def get_tarefa(self):
        """Retorna os dados do formulário como dicionário"""
        nome = self.nome_input.text().strip()
        if not nome:
            QMessageBox.warning(self, "Atenção", "O nome da tarefa é obrigatório!")
            return None

        horario = self.horario_input.time().toString("HH:mm")
        duracao = self.duracao_input.value()
        cor = self.cor_input.currentData()
        barulho = self.barulho_input.currentText()

        subtarefas = []
        for i in range(self.lista_subtarefas.count()):
            subtarefas.append(self.lista_subtarefas.item(i).text())

        descricao = self.descricao_input.toPlainText()

        return {
            "nome": nome,
            "horario": horario,
            "duracao_minutos": duracao,
            "cor": cor,
            "subtarefas": subtarefas,
            "nivel_barulho": barulho,
            "descricao": descricao
        }


# ==================== WIDGETS PERSONALIZADOS ====================

class CardTarefa(QFrame):

    """Card visual da tarefa na linha do tempo"""
    clique = pyqtSignal(object)
    editar = pyqtSignal(object)
    excluir = pyqtSignal(object)

    def __init__(self, tarefa, parent=None):
        super().__init__(parent)
        self.tarefa = tarefa
        self.setup_ui()
        self.setFixedWidth(240)
        self.setMinimumHeight(140)

    def setup_ui(self):
        cor_info = CORES_TEMA[self.tarefa.cor]
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {cor_info['hex']};
                border-radius: 12px;
                margin: 5px;
            }}
            QFrame:hover {{
                border: 2px solid white;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Cabeçalho com horário
        header_layout = QHBoxLayout()
        lbl_horario = QLabel(f"🕐 {self.tarefa.horario}")
        lbl_horario.setStyleSheet(
            "color: black; font-weight: bold; font-size: 14px; "
            "background: rgba(255,255,255,0.35); padding: 2px 8px; border-radius: 10px;"
        )
        header_layout.addWidget(lbl_horario)
        header_layout.addStretch()

        # Botões de edição (aparecem no hover)
        self.btn_editar = QPushButton("✏️")
        self.btn_editar.setFixedSize(30, 30)
        self.btn_editar.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.3);
                border-radius: 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.6);
            }
        """)
        self.btn_editar.clicked.connect(lambda: self.editar.emit(self.tarefa))

        self.btn_excluir = QPushButton("🗑️")
        self.btn_excluir.setFixedSize(30, 30)
        self.btn_excluir.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.3);
                border-radius: 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(231,76,60,0.8);
            }
        """)
        self.btn_excluir.clicked.connect(lambda: self.excluir.emit(self.tarefa))

        header_layout.addWidget(self.btn_editar)
        header_layout.addWidget(self.btn_excluir)
        layout.addLayout(header_layout)

        # Nome
        lbl_nome = QLabel(self.tarefa.nome)
        lbl_nome.setStyleSheet("color: black; font-size: 15px; font-weight: bold;")
        lbl_nome.setWordWrap(True)
        layout.addWidget(lbl_nome)

        # Duração e barulho
        info_layout = QHBoxLayout()
        lbl_duracao = QLabel(f"⏱️ {self.tarefa.duracao_minutos}min")
        lbl_duracao.setStyleSheet(
            "color: black; font-size: 11px; "
            "background: rgba(255,255,255,0.25); padding: 2px 6px; border-radius: 8px;"
        )
        lbl_barulho = QLabel(self.tarefa.nivel_barulho)
        lbl_barulho.setStyleSheet(
            "color: black; font-size: 11px; "
            "background: rgba(255,255,255,0.25); padding: 2px 6px; border-radius: 8px;"
        )
        info_layout.addWidget(lbl_duracao)
        info_layout.addStretch()
        info_layout.addWidget(lbl_barulho)
        layout.addLayout(info_layout)

        # Indicador de subtarefas
        if self.tarefa.subtarefas:
            lbl_sub = QLabel(f"📋 {len(self.tarefa.subtarefas)} passo(s)")
            lbl_sub.setStyleSheet("color: black; font-size: 10px;")
            layout.addWidget(lbl_sub)

        # Check de conclusão
        if self.tarefa.concluida:
            check = QLabel("✅ CONCLUÍDA")
            check.setStyleSheet(
                "color: black; font-size: 10px; "
                "background: rgba(255,255,255,0.4); padding: 3px; border-radius: 4px;"
            )
            layout.addWidget(check)

    def mousePressEvent(self, event):
        self.clique.emit(self.tarefa)

    def enterEvent(self, event):
        """Mostra botões de edição no hover"""
        self.btn_editar.show()
        self.btn_excluir.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Esconde botões de edição"""
        self.btn_editar.hide()
        self.btn_excluir.hide()
        super().leaveEvent(event)


class BotaoIniciar(QPushButton):
    """Botão gigante de iniciar com timer de 5 minutos"""

    def __init__(self, parent=None):
        super().__init__("▶ INICIAR AGORA", parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_timer)
        self.tempo_restante = 0
        self.setup_ui()

    def setup_ui(self):
        self.setFixedSize(320, 90)
        self.setStyleSheet("""
            QPushButton {
                background-color: #50C878;
                color: white;
                font-size: 24px;
                font-weight: bold;
                border-radius: 45px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #3DA867;
            }
            QPushButton:pressed {
                background-color: #2C8C55;
            }
        """)

    def iniciar_temporizador(self, minutos=5):
        self.tempo_restante = minutos * 60
        self.timer.start(1000)
        self.setText(f"⏱️ {minutos}:00")
        self.setStyleSheet(self.styleSheet().replace("background-color: #50C878;", "background-color: #E74C3C;"))

    def atualizar_timer(self):
        if self.tempo_restante > 0:
            self.tempo_restante -= 1
            minutos = self.tempo_restante // 60
            segundos = self.tempo_restante % 60
            self.setText(f"⏱️ {minutos}:{segundos:02d}")
        else:
            self.timer.stop()
            self.setText("✅ CONCLUÍDO! +10 moedas")
            self.setStyleSheet(self.styleSheet().replace("background-color: #E74C3C;", "background-color: #50C878;"))
            QTimer.singleShot(2000, self.resetar_texto)

    def resetar_texto(self):
        self.setText("▶ INICIAR AGORA")


class WidgetSubtarefas(QWidget):
    """Modo Trem - mostra subtarefas da atividade"""

    def __init__(self, tarefa, parent=None):
        super().__init__(parent)
        self.tarefa = tarefa
        self.subtarefa_atual = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Cabeçalho
        lbl_titulo = QLabel(f"🚂 Modo Trem: {self.tarefa.nome}")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFD700;")
        layout.addWidget(lbl_titulo)

        # Spoiler da atividade
        spoiler_frame = QFrame()
        spoiler_frame.setStyleSheet("background-color: #313244; border-radius: 12px; padding: 12px;")
        spoiler_layout = QVBoxLayout(spoiler_frame)

        info_text = f"🔍 O que esperar:\n\n• Duração: {self.tarefa.duracao_minutos} minutos\n• Barulho: {self.tarefa.nivel_barulho}\n"
        if self.tarefa.descricao:
            info_text += f"• Descrição: {self.tarefa.descricao}\n"
        if self.tarefa.subtarefas:
            info_text += f"• Próximo passo: {self.tarefa.subtarefas[0] if self.subtarefa_atual < len(self.tarefa.subtarefas) else 'Finalizar tarefa'}"

        lbl_info = QLabel(info_text)
        lbl_info.setStyleSheet("color: #CDD6F4; font-size: 13px;")
        lbl_info.setWordWrap(True)
        spoiler_layout.addWidget(lbl_info)
        layout.addWidget(spoiler_frame)

        # Lista de subtarefas
        lbl_subtitulo = QLabel("📋 Passo a passo:")
        lbl_subtitulo.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_subtitulo)

        self.lista_sub = QVBoxLayout()
        layout.addLayout(self.lista_sub)

        self.atualizar_lista()

    def atualizar_lista(self):
        # Limpar
        for i in reversed(range(self.lista_sub.count())):
            widget = self.lista_sub.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        for i, sub in enumerate(self.tarefa.subtarefas):
            if i < self.subtarefa_atual:
                cor = "#50C878"
                prefixo = "✅"
                enabled = False
            elif i == self.subtarefa_atual:
                cor = "#89B4FA"
                prefixo = "▶"
                enabled = True
            else:
                cor = "#6C7086"
                prefixo = "◻️"
                enabled = False

            btn = QPushButton(f"{prefixo} {sub}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    padding: 10px;
                    background-color: {cor};
                    color: white;
                    border-radius: 8px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: #B4BEFE;
                }}
            """)
            btn.setEnabled(enabled)
            if enabled:
                btn.clicked.connect(self.completar_subtarefa)
            self.lista_sub.addWidget(btn)

    def completar_subtarefa(self):
        self.subtarefa_atual += 1
        self.atualizar_lista()

        if self.subtarefa_atual >= len(self.tarefa.subtarefas):
            msg = QMessageBox(self)
            msg.setWindowTitle("🎉 Parabéns!")
            msg.setText("Você completou todas as etapas da tarefa!\n\nDeseja marcar como concluída?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if msg.exec() == QMessageBox.StandardButton.Yes:
                self.tarefa.concluida = True
                self.parent().close()


# ==================== APLICAÇÃO PRINCIPAL ====================

class AplicacaoFlow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tarefas = []
        self.perfil_atual = "Normal"
        self.moedas = 0
        self.carregar_dados()
        self.setup_ui()
        self.aplicar_perfil()

    def setup_ui(self):
        self.setWindowTitle("Flow Agenda - Para Autismo e TDAH")
        self.setGeometry(100, 100, 1300, 750)

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        layout_principal = QVBoxLayout(central)
        layout_principal.setSpacing(10)

        # Barra superior com perfil e ações
        barra_superior = QHBoxLayout()

        lbl_perfil = QLabel("🎛️ Perfil de Energia:")
        lbl_perfil.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.combo_perfil = QComboBox()
        self.combo_perfil.addItems(PERFIS_ENERGIA.keys())
        self.combo_perfil.currentTextChanged.connect(self.mudar_perfil)

        # Botões de gerenciamento de tarefas
        self.btn_nova_tarefa = QPushButton("➕ Nova Tarefa")
        self.btn_nova_tarefa.setStyleSheet("""
            QPushButton {
                background-color: #89B4FA;
                color: #1E1E2E;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #B4BEFE;
            }
        """)
        self.btn_nova_tarefa.clicked.connect(self.criar_nova_tarefa)

        self.btn_limpar_concluidas = QPushButton("🧹 Limpar Concluídas")
        self.btn_limpar_concluidas.setStyleSheet("""
            QPushButton {
                background-color: #F38BA8;
                color: #1E1E2E;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F9E2AF;
            }
        """)
        self.btn_limpar_concluidas.clicked.connect(self.limpar_tarefas_concluidas)

        # Moedas
        self.lbl_moedas = QLabel(f"💰 Moedas: {self.moedas}")
        self.lbl_moedas.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFD700;")

        barra_superior.addWidget(lbl_perfil)
        barra_superior.addWidget(self.combo_perfil)
        barra_superior.addStretch()
        barra_superior.addWidget(self.btn_nova_tarefa)
        barra_superior.addWidget(self.btn_limpar_concluidas)
        barra_superior.addWidget(self.lbl_moedas)

        layout_principal.addLayout(barra_superior)

        # Título "Linha do Tempo"
        lbl_titulo = QLabel("📅 Linha do Tempo (deslize para ver os próximos blocos)")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")
        layout_principal.addWidget(lbl_titulo)

        # Área de rolagem horizontal para cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        conteudo_scroll = QWidget()
        self.layout_cards = QHBoxLayout(conteudo_scroll)
        self.layout_cards.setSpacing(15)
        self.layout_cards.addStretch()

        scroll.setWidget(conteudo_scroll)
        layout_principal.addWidget(scroll)

        # Botão Iniciar
        self.botao_iniciar = BotaoIniciar()
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.botao_iniciar)
        btn_layout.addStretch()
        layout_principal.addLayout(btn_layout)

        # Instruções
        lbl_instrucoes = QLabel(
            "💡 Dica: Clique em qualquer card para ver o 'Modo Trem' | ✏️ Passe o mouse para editar/excluir | ➕ Crie novas tarefas")
        lbl_instrucoes.setStyleSheet("color: #6C7086; font-size: 12px; margin-top: 10px;")
        layout_principal.addWidget(lbl_instrucoes)

        # Timer para lembretes
        self.timer_verificacao = QTimer()
        self.timer_verificacao.timeout.connect(self.verificar_lembretes)
        self.timer_verificacao.start(60000)  # Verifica a cada minuto

        # Carregar tarefas de exemplo se não houver dados
        if not self.tarefas:
            self.carregar_tarefas_exemplo()
        self.atualizar_cards()

    def carregar_tarefas_exemplo(self):
        """Cria tarefas de exemplo para demonstração"""
        self.tarefas = [
            Tarefa("☕ Café da manhã", "09:00", 20, "azul", ["Preparar café", "Comer algo", "Guardar louça"],
                   "🌿 Silencioso", "Café da manhã nutritivo para começar o dia"),
            Tarefa("💻 Responder e-mails", "09:30", 60, "verde",
                   ["Abrir e-mail", "Ler mensagens importantes", "Responder 5 e-mails"], "🌿 Silencioso",
                   "Priorizar e-mails do chefe e clientes"),
            Tarefa("🚶 Transição - Escritório", "10:45", 15, "amarelo",
                   ["Guardar notebook", "Separar documentos", "Caminhar até sala"], "🌿 Silencioso",
                   "Momento de mudar de ambiente"),
            Tarefa("🧠 Reunião equipe", "11:00", 45, "vermelho",
                   ["Entrar na sala virtual", "Ativar microfone", "Participar", "Desligar microfone"], "📢 Moderado",
                   "Reunião semanal de alinhamento"),
            Tarefa("🍽️ Almoço", "12:30", 45, "verde", ["Escolher restaurante", "Comer", "Descansar 5min"],
                   "🌿 Silencioso", "Pausa para recarregar energia"),
            Tarefa("📊 Relatório semanal", "14:00", 90, "azul",
                   ["Abrir planilha", "Preencher dados", "Revisar", "Enviar por e-mail"], "🌿 Silencioso",
                   "Relatório para o gestor até as 16h"),
            Tarefa("🎨 Hiperfoco livre", "16:00", 120, "roxo", [], "🌿 Silencioso", "Tempo livre para fazer o que gosta")
        ]

    def atualizar_cards(self):
        """Atualiza a linha do tempo com os cards das tarefas"""
        # Limpar cards existentes
        while self.layout_cards.count() > 1:
            item = self.layout_cards.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Ordenar tarefas por horário
        tarefas_ordenadas = sorted(self.tarefas, key=lambda x: x.horario)

        # Adicionar novos cards
        for tarefa in tarefas_ordenadas:
            card = CardTarefa(tarefa)
            card.clique.connect(self.abrir_modo_trem)
            card.editar.connect(self.editar_tarefa)
            card.excluir.connect(self.excluir_tarefa)
            self.layout_cards.insertWidget(self.layout_cards.count() - 1, card)

    def criar_nova_tarefa(self):
        """Abre diálogo para criar nova tarefa"""
        dialog = DialogoTarefa(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dados = dialog.get_tarefa()
            if dados:
                nova_tarefa = Tarefa(
                    dados["nome"],
                    dados["horario"],
                    dados["duracao_minutos"],
                    dados["cor"],
                    dados["subtarefas"],
                    dados["nivel_barulho"],
                    dados["descricao"]
                )
                self.tarefas.append(nova_tarefa)
                self.atualizar_cards()
                self.salvar_dados()
                QMessageBox.information(self, "Sucesso", f"✅ Tarefa '{nova_tarefa.nome}' criada com sucesso!")

    def editar_tarefa(self, tarefa):
        """Abre diálogo para editar tarefa existente"""
        dialog = DialogoTarefa(tarefa, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dados = dialog.get_tarefa()
            if dados:
                # Atualizar os dados da tarefa
                tarefa.nome = dados["nome"]
                tarefa.horario = dados["horario"]
                tarefa.duracao_minutos = dados["duracao_minutos"]
                tarefa.cor = dados["cor"]
                tarefa.subtarefas = dados["subtarefas"]
                tarefa.nivel_barulho = dados["nivel_barulho"]
                tarefa.descricao = dados["descricao"]
                self.atualizar_cards()
                self.salvar_dados()
                QMessageBox.information(self, "Sucesso", f"✅ Tarefa '{tarefa.nome}' atualizada com sucesso!")

    def excluir_tarefa(self, tarefa):
        """Exclui tarefa após confirmação"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar exclusão")
        msg.setText(f"Tem certeza que deseja excluir a tarefa:\n\n'{tarefa.nome}'?")
        msg.setInformativeText("Esta ação não pode ser desfeita.")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText("✅ Sim, excluir")
        msg.button(QMessageBox.StandardButton.No).setText("❌ Cancelar")

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.tarefas.remove(tarefa)
            self.atualizar_cards()
            self.salvar_dados()
            QMessageBox.information(self, "Excluído", f"🗑️ Tarefa '{tarefa.nome}' foi removida.")

    def limpar_tarefas_concluidas(self):
        """Remove todas as tarefas marcadas como concluídas"""
        tarefas_concluidas = [t for t in self.tarefas if t.concluida]
        if not tarefas_concluidas:
            QMessageBox.information(self, "Nada para limpar", "Não há tarefas concluídas para remover.")
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Limpar tarefas concluídas")
        msg.setText(f"Deseja remover {len(tarefas_concluidas)} tarefa(s) concluída(s)?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.tarefas = [t for t in self.tarefas if not t.concluida]
            self.atualizar_cards()
            self.salvar_dados()
            QMessageBox.information(self, "Limpeza concluída", f"🧹 {len(tarefas_concluidas)} tarefa(s) removida(s).")

    def abrir_modo_trem(self, tarefa):
        """Abre o widget de Modo Trem (subtarefas)"""
        if tarefa.subtarefas:
            from PyQt6.QtWidgets import QDialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"🚂 Modo Trem - {tarefa.nome}")
            dialog.setMinimumSize(450, 550)
            dialog.setStyleSheet("background-color: #1E1E2E; color: #CDD6F4;")

            widget_sub = WidgetSubtarefas(tarefa, dialog)
            layout = QVBoxLayout(dialog)
            layout.addWidget(widget_sub)

            dialog.exec()
            self.atualizar_cards()  # Atualiza para mostrar se foi concluída
        else:
            resposta = QMessageBox.question(
                self,
                "Modo Trem",
                f"'{tarefa.nome}' não tem subtarefas definidas.\n\nDeseja usar o timer de 5 minutos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if resposta == QMessageBox.StandardButton.Yes:
                self.botao_iniciar.iniciar_temporizador()

    def verificar_lembretes(self):
        """Verifica tarefas que estão próximas e envia lembretes educados"""
        agora = datetime.now()
        hora_atual = agora.strftime("%H:%M")

        for tarefa in self.tarefas:
            if not tarefa.concluida:
                # Converter horários para comparar
                hora_tarefa = datetime.strptime(tarefa.horario, "%H:%M").time()
                hora_agora = agora.time()

                # Se está na hora ou atrasou até 15 min
                if hora_agora >= hora_tarefa and (agora - datetime.combine(agora.date(), hora_tarefa)).seconds < 900:
                    if not tarefa.em_andamento:
                        tarefa.em_andamento = True
                        # Lembrete educado
                        msg = QMessageBox(self)
                        msg.setWindowTitle("⏰ Lembrete Educado")
                        msg.setText(
                            f"Ei. Era para você estar em:\n\n'{tarefa.nome}' agora.\n\nAcontece. Quer reagendar ou ignorar?")
                        msg.setStandardButtons(
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Ignore)
                        msg.button(QMessageBox.StandardButton.Yes).setText("✅ Reagendar")
                        msg.button(QMessageBox.StandardButton.No).setText("⏸️ 15 min")
                        msg.button(QMessageBox.StandardButton.Ignore).setText("❌ Ignorar")

                        resposta = msg.exec()
                        if resposta == QMessageBox.StandardButton.Yes:
                            # Reagendar
                            from PyQt6.QtWidgets import QInputDialog
                            novo_horario, ok = QInputDialog.getText(self, "Reagendar", "Novo horário (HH:MM):")
                            if ok and novo_horario:
                                tarefa.horario = novo_horario
                                self.atualizar_cards()
                                QMessageBox.information(self, "Reagendado", f"Tarefa reagendada para {novo_horario}")
                        elif resposta == QMessageBox.StandardButton.No:
                            # Soneca de 15 min
                            QMessageBox.information(self, "Soneca", "Vou lembrar novamente em 15 minutos.")
                        else:
                            tarefa.em_andamento = False

    def mudar_perfil(self, perfil):
        """Muda o perfil de energia do app"""
        self.perfil_atual = perfil
        self.aplicar_perfil()

    def aplicar_perfil(self):
        perfil = PERFIS_ENERGIA[self.perfil_atual]

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {perfil['bg_color']};
            }}
            QLabel, QPushButton:not(.BotaoIniciar) {{
                color: {perfil['text_color']};
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QComboBox, QPushButton {{
                background-color: {perfil['bg_color']};
                color: {perfil['text_color']};
                padding: 5px;
                border: 1px solid #6C7086;
                border-radius: 8px;
            }}
        """)

    def carregar_dados(self):
        """Carrega dados salvos (se existirem)"""
        if os.path.exists("flow_agenda.json"):
            try:
                with open("flow_agenda.json", "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.tarefas = [Tarefa.from_dict(t) for t in dados.get("tarefas", [])]
                    self.moedas = dados.get("moedas", 0)
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")

    def salvar_dados(self):
        """Salva os dados do app"""
        dados = {
            "tarefas": [t.to_dict() for t in self.tarefas],
            "moedas": self.moedas
        }
        try:
            with open("flow_agenda.json", "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")

    def closeEvent(self, event):
        """Salva ao fechar"""
        self.salvar_dados()
        event.accept()


# ==================== MAIN ====================

def main():
    app = QApplication(sys.argv)

    # Configurar fonte global
    fonte = QFont("Segoe UI", 10)
    app.setFont(fonte)

    # Criar e mostrar janela
    window = AplicacaoFlow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()