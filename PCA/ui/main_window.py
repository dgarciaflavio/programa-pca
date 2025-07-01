# ui/main_window.py - Versão com PySide6

import sys
import os
import math
from datetime import datetime
import pyperclip
import pandas as pd

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QGroupBox,
    QGridLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenuBar, QMessageBox, QMenu, QDateEdit, QHBoxLayout,
    QInputDialog
)
from PySide6.QtGui import QAction, QCursor
from PySide6.QtCore import Qt, QDate

from services.parser import load_all_years
from services.preferencias import carregar_preferencias, salvar_preferencias
from services.downloader import download_csv_files

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Consulta PCA - v7.7 (Final)")
        self.setGeometry(100, 100, 1200, 800)

        self.df_por_ano = {}
        self.abas_info = {}
        self.clicked_info = {} # Armazena informações do clique do mouse
        
        self.notebook = QTabWidget()
        self.setCentralWidget(self.notebook)
        
        self._criar_menu()
        
        self.carregar_dados_iniciais()

    def _criar_menu(self):
        menu_bar = self.menuBar()
        dados_menu = menu_bar.addMenu("&Dados")
        
        acao_atualizar = QAction("Atualizar Todos os Dados", self)
        acao_atualizar.triggered.connect(self.atualizar_dados_manual)
        dados_menu.addAction(acao_atualizar)
        
        dados_menu.addSeparator()

        acao_adicionar = QAction("Adicionar Ano...", self)
        acao_adicionar.triggered.connect(self.adicionar_ano)
        dados_menu.addAction(acao_adicionar)

        acao_excluir = QAction("Excluir Ano...", self)
        acao_excluir.triggered.connect(self.excluir_ano)
        dados_menu.addAction(acao_excluir)

    def with_loading_cursor(func):
        def wrapper(self, *args, **kwargs):
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                return func(self, *args, **kwargs)
            finally:
                QApplication.restoreOverrideCursor()
        return wrapper

    @with_loading_cursor
    def carregar_dados_iniciais(self):
        try:
            self.df_por_ano = load_all_years()
            self.recriar_abas()
        except Exception as e:
            QMessageBox.critical(self, "Erro Inesperado", f"Ocorreu um erro ao carregar os dados: {e}")

    @with_loading_cursor
    def atualizar_dados_manual(self):
        if QMessageBox.question(self, "Confirmar Atualização", r"Isso fará o download e otimização dos dados.\Deseja continuar?") == QMessageBox.Yes:
            try:
                download_csv_files()
                self.carregar_dados_iniciais()
            except Exception as e:
                QMessageBox.critical(self, "Erro na Atualização", f"Não foi possível atualizar os dados: {e}")

    def adicionar_ano(self):
        ano, ok1 = QInputDialog.getText(self, "Adicionar Ano", "Digite o ano (ex: 2027):")
        if ok1 and ano:
            if not ano.isdigit() or len(ano) != 4:
                QMessageBox.warning(self, "Entrada Inválida", "O ano deve ser um número de 4 dígitos.")
                return
            url, ok2 = QInputDialog.getText(self, "Adicionar URL", f"Cole a URL do arquivo CSV para o ano {ano}:")
            if ok2 and url:
                prefs = carregar_preferencias()
                prefs['data_sources'][ano] = url
                salvar_preferencias(prefs)
                QMessageBox.information(self, "Sucesso", f"Ano {ano} adicionado. Use 'Dados -> Atualizar' para baixar as informações.")

    def excluir_ano(self):
        prefs = carregar_preferencias()
        anos = list(prefs['data_sources'].keys())
        if not anos:
            QMessageBox.information(self, "Excluir Ano", "Nenhum ano para excluir.")
            return
            
        ano_para_excluir, ok = QInputDialog.getItem(self, "Excluir Ano", "Selecione o ano para excluir:", anos, 0, False)
        
        if ok and ano_para_excluir:
            if QMessageBox.question(self, "Confirmação", f"Tem certeza que deseja excluir o ano {ano_para_excluir} e seus dados permanentemente?") == QMessageBox.Yes:
                del prefs['data_sources'][ano_para_excluir]
                if ano_para_excluir in prefs.get('filters', {}):
                    del prefs['filters'][ano_para_excluir]
                salvar_preferencias(prefs)
                caminho_arquivo = os.path.join("data", f"pca_{ano_para_excluir}.csv")
                try:
                    if os.path.exists(caminho_arquivo): os.remove(caminho_arquivo)
                except OSError as e:
                    QMessageBox.critical(self, "Erro de Arquivo", f"Não foi possível excluir o arquivo {caminho_arquivo}: {e}")
                QMessageBox.information(self, "Sucesso", f"Ano {ano_para_excluir} excluído com sucesso.")
                self.carregar_dados_iniciais()

    def recriar_abas(self):
        self.notebook.clear()
        self.abas_info.clear()
        for ano, df in self.df_por_ano.items():
            if not df.empty:
                self.criar_aba(ano, df)

    def criar_aba(self, ano, df_original):
        aba = QWidget()
        layout_principal = QVBoxLayout(aba)
        self.notebook.addTab(aba, str(ano))
        
        if 'Data Desejada' in df_original.columns:
            df_original['data_datetime'] = pd.to_datetime(
                df_original['Data Desejada'], errors='coerce', dayfirst=True
            )
        
        info_aba = {
            'df_original': df_original, 'df_resultado': df_original.copy(), 'entradas': {},
            'data_desejada_entry': None, 'PAGE_SIZE': 50, 'current_page': 1,
            'sort_column': None, 'sort_order': Qt.AscendingOrder
        }
        self.abas_info[ano] = info_aba

        filtro_groupbox = QGroupBox("Filtros")
        filtro_layout = QGridLayout(filtro_groupbox)
        layout_principal.addWidget(filtro_groupbox)
        
        colunas_disponiveis = ["UASG", "Identificador da Futura Contratação", "Descrição do Item", "Valor Total Estimado (R$)"]
        campos_filtro = [col for col in colunas_disponiveis if col in df_original.columns]
        
        row, col = 0, 0
        for campo in campos_filtro:
            filtro_layout.addWidget(QLabel(f"{campo.replace(' (R$)', '')}:"), row, col * 2)
            entry = QLineEdit()
            entry.setPlaceholderText(f"Filtrar por {campo}...")
            filtro_layout.addWidget(entry, row, col * 2 + 1)
            info_aba['entradas'][campo] = entry
            col += 1
            if col > 1: col = 0; row += 1
        
        filtro_layout.addWidget(QLabel("Data Desejada:"), row, 0)
        data_entry = QDateEdit()
        data_entry.setCalendarPopup(True)
        data_entry.setDisplayFormat("dd/MM/yyyy")
        data_entry.setSpecialValueText(" ")
        data_entry.setDate(data_entry.minimumDate())
        filtro_layout.addWidget(data_entry, row, 1)
        info_aba['data_desejada_entry'] = data_entry

        btn_limpar = QPushButton("Limpar Filtros 🗑️")
        filtro_layout.addWidget(btn_limpar, row + 1, 0, 1, 4)
        
        colunas_desejadas = ['Unidade Responsável', 'UASG', 'Id do item no PCA', 'Categoria do Item','Identificador da Futura Contratação', 'Classificação do Catálogo','Código da Classificação Superior (Classe/Grupo)', 'Nome do PDM do Item','Código do Item', 'Descrição do Item', 'Quantidade Estimada','Valor Total Estimado (R$)', 'Data Desejada']
        colunas_tabela = [c for c in colunas_desejadas if c in df_original.columns]
        
        tabela = QTableWidget()
        tabela.setColumnCount(len(colunas_tabela))
        tabela.setHorizontalHeaderLabels(colunas_tabela)
        tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        tabela.setSelectionBehavior(QTableWidget.SelectRows)
        tabela.verticalHeader().setVisible(False)
        tabela.setAlternatingRowColors(True)
        tabela.horizontalHeader().setStretchLastSection(True)
        tabela.horizontalHeader().sectionClicked.connect(lambda logical_index, a=ano: classificar_coluna(logical_index, a))
        layout_principal.addWidget(tabela)

        rodape_layout = QHBoxLayout()
        layout_principal.addLayout(rodape_layout)
        lbl_registros_e_valor = QLabel("Registros: 0 | Valor Total: R$ 0,00")
        btn_anterior = QPushButton("<< Anterior")
        btn_proxima = QPushButton("Próxima >>")
        lbl_pagina = QLabel("Página 1 de 1")
        
        rodape_layout.addWidget(lbl_registros_e_valor)
        rodape_layout.addStretch()
        rodape_layout.addWidget(btn_anterior)
        rodape_layout.addWidget(lbl_pagina)
        rodape_layout.addWidget(btn_proxima)
        
        def atualizar_tabela():
            QApplication.setOverrideCursor(Qt.WaitCursor)
            tabela.setSortingEnabled(False)
            tabela.setRowCount(0)
            df_paginado = info_aba['df_resultado']
            total_items = len(df_paginado)
            total_pages = math.ceil(total_items / info_aba['PAGE_SIZE']) if total_items > 0 else 1
            if info_aba['current_page'] > total_pages: info_aba['current_page'] = total_pages
            start_index = (info_aba['current_page'] - 1) * info_aba['PAGE_SIZE']
            end_index = start_index + info_aba['PAGE_SIZE']
            df_pagina = df_paginado.iloc[start_index:end_index]
            tabela.setRowCount(len(df_pagina))
            for i, (_, row) in enumerate(df_pagina[colunas_tabela].iterrows()):
                for j, value in enumerate(row):
                    tabela.setItem(i, j, QTableWidgetItem(str(value)))
            soma_valores = pd.to_numeric(df_paginado['Valor Total Estimado (R$)'].str.replace(',', '.', regex=False), errors='coerce').sum()
            lbl_registros_e_valor.setText(f"Registros: {total_items} | Valor Total: R$ {soma_valores:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            lbl_pagina.setText(f"Página {info_aba['current_page']} de {total_pages}")
            btn_anterior.setEnabled(info_aba['current_page'] > 1)
            btn_proxima.setEnabled(info_aba['current_page'] < total_pages)
            tabela.setSortingEnabled(True)
            QApplication.restoreOverrideCursor()
        
        def aplicar_filtros():
            df_filtrado = info_aba['df_original'].copy()
            for campo, widget in info_aba['entradas'].items():
                valor = widget.text()
                if valor:
                    df_filtrado = df_filtrado[df_filtrado[campo].astype(str).str.contains(valor, case=False, na=False)]
            data_selecionada = info_aba['data_desejada_entry'].date()
            if data_selecionada != data_entry.minimumDate():
                py_date = data_selecionada.toPython()
                if 'data_datetime' in df_filtrado.columns:
                    df_filtrado = df_filtrado.dropna(subset=['data_datetime'])
                    df_filtrado = df_filtrado[df_filtrado['data_datetime'].dt.date == py_date]
            info_aba['df_resultado'] = df_filtrado
            info_aba['current_page'] = 1
            atualizar_tabela()

        def limpar_filtros():
            for widget in info_aba['entradas'].values():
                if widget.isReadOnly(): continue
                widget.textChanged.disconnect(aplicar_filtros)
                widget.clear()
                widget.textChanged.connect(aplicar_filtros)
            
            info_aba['data_desejada_entry'].dateChanged.disconnect(aplicar_filtros)
            info_aba['data_desejada_entry'].setDate(info_aba['data_desejada_entry'].minimumDate())
            info_aba['data_desejada_entry'].dateChanged.connect(aplicar_filtros)
            
            aplicar_filtros()

        def pagina_anterior():
            if info_aba['current_page'] > 1:
                info_aba['current_page'] -= 1
                atualizar_tabela()

        def proxima_pagina():
            total_items = len(info_aba['df_resultado'])
            total_pages = math.ceil(total_items / info_aba['PAGE_SIZE'])
            if info_aba['current_page'] < total_pages:
                info_aba['current_page'] += 1
                atualizar_tabela()

        def classificar_coluna(logical_index, ano_aba):
            info_aba_sort = self.abas_info[ano_aba]
            col_name = colunas_tabela[logical_index]
            if info_aba_sort['sort_column'] == col_name:
                info_aba_sort['sort_order'] = Qt.DescendingOrder if info_aba_sort['sort_order'] == Qt.AscendingOrder else Qt.AscendingOrder
            else:
                info_aba_sort['sort_order'] = Qt.AscendingOrder
            tabela.horizontalHeader().setSortIndicator(logical_index, info_aba_sort['sort_order'])
            info_aba_sort['sort_column'] = col_name
            ascending = (info_aba_sort['sort_order'] == Qt.AscendingOrder)
            try:
                col_numeric = pd.to_numeric(info_aba_sort['df_resultado'][col_name].str.replace(',', '.', regex=False), errors='coerce')
                if not col_numeric.isna().all():
                    info_aba_sort['df_resultado'] = info_aba_sort['df_resultado'].iloc[col_numeric.sort_values(ascending=ascending).index]
                else: raise ValueError()
            except (AttributeError, ValueError):
                info_aba_sort['df_resultado'] = info_aba_sort['df_resultado'].sort_values(by=col_name, ascending=ascending, na_position='last')
            info_aba_sort['current_page'] = 1
            atualizar_tabela()

        def copiar_id_contratacao(item_clicado):
            if 'Identificador da Futura Contratação' in colunas_tabela:
                coluna_id_index = colunas_tabela.index('Identificador da Futura Contratação')
                item_id = tabela.item(item_clicado.row(), coluna_id_index)
                if item_id:
                    pyperclip.copy(item_id.text())
                    QMessageBox.information(aba, "Copiado", f"O ID '{item_id.text()}' foi copiado.")

        def filtrar_por_valor_celula():
            for widget in info_aba['entradas'].values():
                widget.textChanged.disconnect(aplicar_filtros)
            info_aba['data_desejada_entry'].dateChanged.disconnect(aplicar_filtros)
            for campo, widget in info_aba['entradas'].items():
                 if not widget.isReadOnly(): widget.clear()
            info_aba['data_desejada_entry'].setDate(info_aba['data_desejada_entry'].minimumDate())
            col_name = self.clicked_info['col_name']
            value = self.clicked_info['value']
            info_aba['entradas'][col_name].setText(value)
            for widget in info_aba['entradas'].values():
                widget.textChanged.connect(aplicar_filtros)
            info_aba['data_desejada_entry'].dateChanged.connect(aplicar_filtros)
            aplicar_filtros()

        def mostrar_menu_contexto(position):
            item = tabela.itemAt(position)
            if not item: return
            menu = QMenu()
            valor_celula = item.text()
            
            col_name = colunas_tabela[item.column()]
            self.clicked_info = {'col_name': col_name, 'value': valor_celula}

            acao_copiar_celula = QAction(f"Copiar \"{valor_celula[:30]}...\"", menu)
            acao_copiar_celula.triggered.connect(lambda: pyperclip.copy(valor_celula))
            menu.addAction(acao_copiar_celula)
            
            valores_linha = [tabela.item(item.row(), c).text() for c in range(tabela.columnCount())]
            acao_copiar_linha = QAction("Copiar Linha Inteira", menu)
            acao_copiar_linha.triggered.connect(lambda: pyperclip.copy("\t".join(valores_linha)))
            menu.addAction(acao_copiar_linha)
            
            if col_name in info_aba['entradas'] and not info_aba['entradas'][col_name].isReadOnly():
                menu.addSeparator()
                # --- CORREÇÃO AQUI: Mostrando o valor da célula no menu ---
                acao_filtrar = QAction(f"Filtrar por \"{valor_celula[:30]}...\"", menu)
                acao_filtrar.triggered.connect(filtrar_por_valor_celula)
                menu.addAction(acao_filtrar)
            
            menu.exec(tabela.viewport().mapToGlobal(position))

        tabela.setContextMenuPolicy(Qt.CustomContextMenu)
        tabela.customContextMenuRequested.connect(mostrar_menu_contexto)
        tabela.itemDoubleClicked.connect(copiar_id_contratacao)
        
        btn_limpar.clicked.connect(limpar_filtros)
        btn_anterior.clicked.connect(pagina_anterior)
        btn_proxima.clicked.connect(proxima_pagina)
        
        for entry_widget in info_aba['entradas'].values():
            entry_widget.textChanged.connect(aplicar_filtros)
        data_entry.dateChanged.connect(aplicar_filtros)

        if 'UASG' in info_aba['entradas']:
            uasg_entry = info_aba['entradas']['UASG']
            uasg_entry.setText('250052')
            uasg_entry.setReadOnly(True)
        
        aplicar_filtros()

def iniciar_interface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())