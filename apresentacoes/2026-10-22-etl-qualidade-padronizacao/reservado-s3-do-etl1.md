# Par de slides S3 retirado do ETL I (18/10/2026)

Usar como introdução ao MinIO (API S3) na aula ETL II. Os trechos abaixo vêm de `../2026-10-20-etl-fontes-integracao/deck.html` e seguem a mesma estrutura (`FONTES_MUNDO_REAL`, `AJUDA_CODIGOS`, ícone `s3` em `ICONES_FONTES`, arquivo `lambda_s3.py`). Na ETL II, o MinIO será destino da carga; adaptar o texto que trata o S3 como fonte acionada por evento.

## Ajuda do código

```js
    s3: [
      { inicio:3, fim:3, texto:'boto3 cria o cliente S3. A biblioteca obtém as credenciais do ambiente de execução, por exemplo pela identidade atribuída à função Lambda.' },
      { inicio:5, fim:8, texto:'A integração configurada chama handler com evento e contexto. Records pode trazer vários registros; o laço processa cada um deles.' },
      { inicio:9, fim:11, texto:'Bucket e chave identificam o objeto. unquote_plus decodifica a chave da notificação antes de get_object buscar seu conteúdo.' },
      { inicio:12, fim:14, texto:'Body é um fluxo de bytes. read lê o conteúdo e with fecha o fluxo. Os bytes retornados ainda precisam ser interpretados e carregados.' }
    ]
```

## Fonte

```js
    {
      id:'s3', nome:'Amazon S3', perfil:'Exemplo: fonte interna', detalhe:'CSV · JSON · Parquet · imagens',
      gatilho:'Objeto criado', executor:'S3 → Lambda', chamada:'handler(evento)', saida:'Conteúdo do objeto',
      legenda:'O evento aponta bucket e chave; o script busca o objeto.',
      biblioteca:'AWS Lambda + Boto3', url:'https://docs.aws.amazon.com/lambda/latest/dg/with-s3-example.html',
      pontos:[['Localizar','Bucket e chave vêm do evento.'],['Capturar','Boto3 busca o corpo do objeto.'],['Entregar','Bytes seguem para leitura e carga.']],
      codigo:`import boto3
from urllib.parse import unquote_plus

s3 = boto3.client("s3")

def handler(evento, contexto):
    objetos = []
    for registro in evento["Records"]:
        origem = registro["s3"]
        objeto = s3.get_object(
            Bucket=origem["bucket"]["name"],
            Key=unquote_plus(origem["object"]["key"]))
        with objeto["Body"] as corpo:
            objetos.append(corpo.read())
    return objetos`,
      notas:'Cenário didático: arquivos internos são armazenados em um bucket S3. O bucket está configurado para notificar uma função Lambda em eventos ObjectCreated. O nome handler não configura sozinho o gatilho: a integração S3-Lambda e o ponto de entrada do runtime são definidos no ambiente. A função recebe evento e contexto; por isso o código possui dois parâmetros mesmo que o diagrama abrevie a chamada. Para cada registro de Records, extrai bucket e chave. A chave vem codificada na notificação: unquote_plus a decodifica antes de get_object. A função lê e fecha o StreamingBody e retorna bytes; a leitura do formato (CSV, JSON, Parquet, imagem) e a carga posterior são outras etapas. O exemplo usa pequenos objetos em memória. Boto3 resolve credenciais pelo ambiente de execução, como a role da Lambda. S3 é armazenamento de objetos, não um banco NoSQL de documentos. Na aula ETL II, o MinIO, que oferece a mesma API S3 localmente, será a área de chegada; nesta aula o laboratório grava o CSV em uma pasta local. Ele pode conter dados internos ou externos; neste cenário representa arquivos internos. As notificações podem se repetir: o processamento de produção precisa controlar reexecuções, sem presumir entrega exatamente uma vez. Nenhuma conta ou bucket real é usado.'
    }
```
