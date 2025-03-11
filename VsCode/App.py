import sqlite3
import os
import re
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Caminhos dos bancos
pasta_banco = r"D:/VsCode/BancoDeDados"
os.makedirs(pasta_banco, exist_ok=True)  # Cria a pasta se não existir

caminho_cadastro = os.path.join(pasta_banco, "Cadastro.db")
caminho_gostos = os.path.join(pasta_banco, "Gostos.db")

# Funções de validação
def validar_nome(nome):
    return nome.isalpha()

def validar_idade(idade):
    return idade.isdigit()

def validar_email(email):
    padrao = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(padrao, email)

# Funções de banco de dados
def criar_conexao(caminho):
    conn = sqlite3.connect(caminho)
    return conn, conn.cursor()

def criar_tabelas():
    conn_cadastro, cursor_cadastro = criar_conexao(caminho_cadastro)
    cursor_cadastro.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            idade INTEGER NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    ''')

    conn_gostos, cursor_gostos = criar_conexao(caminho_gostos)
    cursor_gostos.execute('''
        CREATE TABLE IF NOT EXISTS gostos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            gosto TEXT NOT NULL,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
            UNIQUE(usuario_id, tipo, gosto)
        )
    ''')

    # Tabela para armazenar os matches
    conn_matches, cursor_matches = criar_conexao(caminho_cadastro)
    cursor_matches.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario1_id INTEGER NOT NULL,
            usuario2_id INTEGER NOT NULL,
            quantidade_comum INTEGER NOT NULL,
            FOREIGN KEY(usuario1_id) REFERENCES usuarios(id),
            FOREIGN KEY(usuario2_id) REFERENCES usuarios(id)
        )
    ''')

    return conn_cadastro, cursor_cadastro, conn_gostos, cursor_gostos, conn_matches, cursor_matches

def verificar_email_existente(cursor, email):
    cursor.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
    return cursor.fetchone()

def adicionar_usuario(cursor, conn, nome, idade, email):
    try:
        cursor.execute('''
            INSERT INTO usuarios (nome, idade, email) 
            VALUES (?, ?, ?)
        ''', (nome, idade, email))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        print(f"❌ Erro de integridade: {e}")
        conn.rollback()
        return None

def adicionar_gosto(cursor, conn, usuario_id, tipo, gosto):
    try:
        cursor.execute('''
            INSERT INTO gostos (usuario_id, tipo, gosto) 
            VALUES (?, ?, ?)
        ''', (usuario_id, tipo, gosto))
        conn.commit()
        print(f"✅ Gosto '{gosto}' de tipo '{tipo}' adicionado com sucesso!")
    except sqlite3.IntegrityError:
        print(f"❌ Gosto '{gosto}' de tipo '{tipo}' já foi registrado para este usuário.")

# Conectar ao banco de cadastro
def get_db_connection():
    conn = sqlite3.connect(caminho_cadastro)
    conn.row_factory = sqlite3.Row
    return conn

# Rota para cadastro de usuário
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']
        email = request.form['email']

        if not validar_nome(nome) or not validar_idade(idade) or not validar_email(email):
            return "Dados inválidos, tente novamente!"

        # Inserir usuário no banco
        conn = get_db_connection()
        cursor = conn.cursor()
        if verificar_email_existente(cursor, email):
            return "Email já cadastrado!"

        usuario_id = adicionar_usuario(cursor, conn, nome, int(idade), email)
        conn.close()

        if usuario_id:
            print(f"✅ Cadastro realizado com sucesso! Seu ID de usuário é {usuario_id}.")
            return redirect(url_for('adicionar_gostos', usuario_id=usuario_id))
        else:
            return "Erro ao cadastrar usuário!"

    return render_template('index.html')

# Página de adicionar gostos
@app.route('/adicionar_gostos/<int:usuario_id>', methods=['GET', 'POST'])
def adicionar_gostos(usuario_id):
    if request.method == 'POST':
        tipo = request.form['tipo']
        gosto = request.form['gosto']

        # Adicionar gosto no banco
        conn = sqlite3.connect(caminho_gostos)
        cursor = conn.cursor()
        adicionar_gosto(cursor, conn, usuario_id, tipo, gosto)
        conn.close()

        # Redirecionar para a mesma página
        return redirect(url_for('adicionar_gostos', usuario_id=usuario_id))

    # Verificar o número de gostos já cadastrados para o usuário
    conn = sqlite3.connect(caminho_gostos)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM gostos WHERE usuario_id = ?', (usuario_id,))
    quantidade_gostos = cursor.fetchone()[0]
    conn.close()

    # Se o usuário tiver 3 ou mais gostos, mostra o botão de pular
    pode_pular = quantidade_gostos >= 3

    return render_template('adicionar_gostos.html', usuario_id=usuario_id, pode_pular=pode_pular)

# Página de resultados de matches
@app.route('/matches', methods=['GET', 'POST'])
def matches():
    if request.method == 'POST':
        usuario1_id = int(request.form['usuario1_id'])
        usuario2_id = int(request.form['usuario2_id'])

        # Buscar os gostos dos dois usuários
        conn = sqlite3.connect(caminho_gostos)
        cursor = conn.cursor()

        cursor.execute("SELECT tipo, gosto FROM gostos WHERE usuario_id = ?", (usuario1_id,))
        gostos_usuario1 = cursor.fetchall()

        cursor.execute("SELECT tipo, gosto FROM gostos WHERE usuario_id = ?", (usuario2_id,))
        gostos_usuario2 = cursor.fetchall()

        # Comparar gostos dos usuários
        gostos_comum = []
        for tipo, gosto in gostos_usuario1:
            if (tipo, gosto) in gostos_usuario2:
                gostos_comum.append((tipo, gosto))

        quantidade_comum = len(gostos_comum)

        # Se houver match, armazenar no banco
        if quantidade_comum > 0:
            # Conectar à tabela de matches para registrar o match
            conn_matches = sqlite3.connect(caminho_cadastro)
            cursor_matches = conn_matches.cursor()
            cursor_matches.execute('''
                INSERT INTO matches (usuario1_id, usuario2_id, quantidade_comum)
                VALUES (?, ?, ?)
            ''', (usuario1_id, usuario2_id, quantidade_comum))
            conn_matches.commit()
            conn_matches.close()

        conn.close()

    # Buscar todos os matches armazenados
    conn_matches = sqlite3.connect(caminho_cadastro)
    cursor_matches = conn_matches.cursor()
    cursor_matches.execute('''
        SELECT m.usuario1_id, m.usuario2_id, m.quantidade_comum, u1.nome as nome1, u1.idade as idade1, u2.nome as nome2, u2.idade as idade2
        FROM matches m
        JOIN usuarios u1 ON m.usuario1_id = u1.id
        JOIN usuarios u2 ON m.usuario2_id = u2.id
    ''')
    matches = cursor_matches.fetchall()
    conn_matches.close()

    return render_template('matches.html', matches=matches)

if __name__ == '__main__':
    criar_tabelas()  # Cria as tabelas ao iniciar a aplicação
    app.run(debug=True)
