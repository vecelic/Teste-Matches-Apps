import sqlite3
import os

# Definir o caminho da pasta do banco de dados
pasta_banco = r"D:/VsCode/BancoDeDados"
os.makedirs(pasta_banco, exist_ok=True)  # Cria a pasta se não existir

# Caminhos dos bancos
caminho_cadastro = os.path.join(pasta_banco, "Cadastro.db")
caminho_gostos = os.path.join(pasta_banco, "Gostos.db")

# Conectar ao banco de cadastro
conn_cadastro = sqlite3.connect(caminho_cadastro)
cursor_cadastro = conn_cadastro.cursor()

# Conectar ao banco de gostos
conn_gostos = sqlite3.connect(caminho_gostos)
cursor_gostos = conn_gostos.cursor()

# 📌 Listar usuários
cursor_cadastro.execute("SELECT id, nome FROM usuarios")
usuarios = cursor_cadastro.fetchall()

if len(usuarios) < 2:
    print("❌ Não há usuários suficientes para realizar a comparação de matches!")
    conn_cadastro.close()
    conn_gostos.close()
    exit()

# 📌 Exibir usuários para escolha
print("\nUsuários disponíveis para encontrar matches:")
for id, nome in usuarios:
    print(f"{id} - {nome}")

# 📌 Escolher dois usuários para realizar o match
usuario1_id = input("\nDigite o ID do primeiro usuário para comparação: ")
usuario2_id = input("Digite o ID do segundo usuário para comparação: ")

# Verificar se os IDs são válidos
if usuario1_id == usuario2_id:
    print("❌ Não é possível comparar o mesmo usuário com ele mesmo!")
    conn_cadastro.close()
    conn_gostos.close()
    exit()

# 📌 Buscar os gostos dos dois usuários
cursor_gostos.execute("SELECT tipo, gosto FROM gostos WHERE usuario_id = ?", (usuario1_id,))
gostos_usuario1 = cursor_gostos.fetchall()

cursor_gostos.execute("SELECT tipo, gosto FROM gostos WHERE usuario_id = ?", (usuario2_id,))
gostos_usuario2 = cursor_gostos.fetchall()

# 📌 Comparar gostos dos usuários
gostos_comum = set(gostos_usuario1) & set(gostos_usuario2)
quantidade_comum = len(gostos_comum)

# 📌 Exibir resultado do match
if quantidade_comum > 0:
    print(f"\n🎉 Match encontrado entre {usuario1_id} e {usuario2_id}!")
    print(f"👥 Gostos em comum: {quantidade_comum}")
    print("Gostos em comum:")
    for tipo, gosto in gostos_comum:
        print(f"- {tipo.capitalize()}: {gosto}")
else:
    print("\n❌ Nenhum match encontrado entre os dois usuários.")

# Fechar conexões
conn_cadastro.close()
conn_gostos.close()
