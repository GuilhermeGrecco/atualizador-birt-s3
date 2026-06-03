import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3

app = Flask(__name__)
# O CORS permite que a sua página HTML converse com esta API
CORS(app)

# ================= Configurações =================
NOME_DO_BUCKET = 'el-gpicloud-files'

# Puxando os caminhos diretamente das variáveis de ambiente do Render
CAMINHOS_S3 = {
    'homologacao': os.getenv('S3_PATH_HOMOLOGACAO'),
    'producao': os.getenv('S3_PATH_PRODUCAO')
}
# =================================================

# Inicializa o cliente da AWS usando as credenciais configuradas no Render
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

    if not ambiente or ambiente not in ['homologacao', 'producao', 'ambos']:
        return jsonify({'erro': 'Ambiente inválido ou não informado.'}), 400

    destinos = []
    if ambiente == 'ambos':
        destinos = [CAMINHOS_S3['homologacao'], CAMINHOS_S3['producao']]
    else:
        destinos = [CAMINHOS_S3[ambiente]]

    resultados = []

    for arquivo in arquivos:
        if arquivo and arquivo.filename.endswith('.rptdesign'):
            for destino in destinos:
                caminho_completo_s3 = f"{destino}{arquivo.filename}"
                
                try:
                    s3_client.upload_fileobj(arquivo, NOME_DO_BUCKET, caminho_completo_s3)
                    resultados.append(f"✅ {arquivo.filename} -> {caminho_completo_s3}")
                except Exception as e:
                    resultados.append(f"❌ Erro em {arquivo.filename} -> {caminho_completo_s3}: {str(e)}")
        else:
            resultados.append(f"⚠️ Ignorado (formato inválido): {arquivo.filename}")

    return jsonify({
        'mensagem': 'Processamento finalizado.',
        'detalhes': resultados
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
