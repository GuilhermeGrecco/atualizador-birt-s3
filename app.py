import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3

app = Flask(__name__)
CORS(app)

# ================= Configurações =================
NOME_DO_BUCKET = 'el-gpicloud-files'

# Caminhos para Relatórios (Padrão)
CAMINHOS_S3_RELATORIO = {
    'homologacao': os.getenv('S3_PATH_HOMOLOGACAO'),
    'producao': os.getenv('S3_PATH_PRODUCAO')
}

# Caminhos para Masterpages
CAMINHOS_S3_MASTERPAGE = {
    'homologacao': os.getenv('S3_PATH_MASTERPAGE_HOMOLOGACAO'),
    'producao': os.getenv('S3_PATH_MASTERPAGE_PRODUCAO')
}
# =================================================

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

@app.route('/upload', methods=['POST'])
def receber_arquivos():
    if 'arquivos' not in request.files:
        return jsonify({'erro': 'Nenhum arquivo recebido.'}), 400
    
    arquivos = request.files.getlist('arquivos')
    ambiente = request.form.get('ambiente')
    tipo_arquivo = request.form.get('tipo_arquivo')

    if not ambiente or ambiente not in ['homologacao', 'producao', 'ambos']:
        return jsonify({'erro': 'Ambiente inválido ou não informado.'}), 400
        
    if not tipo_arquivo or tipo_arquivo not in ['relatorio', 'masterpage']:
        return jsonify({'erro': 'Tipo de arquivo inválido ou não informado.'}), 400

    caminhos_ativos = CAMINHOS_S3_RELATORIO if tipo_arquivo == 'relatorio' else CAMINHOS_S3_MASTERPAGE

    destinos = []
    if ambiente == 'ambos':
        destinos = [caminhos_ativos['homologacao'], caminhos_ativos['producao']]
    else:
        destinos = [caminhos_ativos[ambiente]]

    resultados = []

    for arquivo in arquivos:
        if arquivo and arquivo.filename.endswith('.rptdesign'):
            try:
                # LER O ARQUIVO NA MEMÓRIA UMA ÚNICA VEZ
                conteudo_arquivo = arquivo.read()
                
                for destino in destinos:
                    caminho_completo_s3 = f"{destino}{arquivo.filename}"
                    
                    try:
                        # Envia os dados armazenados na memória usando put_object
                        s3_client.put_object(
                            Bucket=NOME_DO_BUCKET,
                            Key=caminho_completo_s3,
                            Body=conteudo_arquivo
                        )
                        resultados.append(f"✅ {arquivo.filename} -> {caminho_completo_s3}")
                    except Exception as e:
                        resultados.append(f"❌ Erro em {arquivo.filename} -> {caminho_completo_s3}: {str(e)}")
            except Exception as e:
                resultados.append(f"❌ Erro ao ler o arquivo {arquivo.filename}: {str(e)}")
        else:
            resultados.append(f"⚠️ Ignorado (formato inválido): {arquivo.filename}")

    return jsonify({
        'mensagem': 'Processamento finalizado.',
        'detalhes': resultados
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
