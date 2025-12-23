# Gerando Chaves ECDSA com OpenSSL

Este guia detalha o processo de geração de pares de chaves públicas e privadas ECDSA utilizando a ferramenta OpenSSL. As chaves ECDSA são amplamente utilizadas em sistemas de criptografia e autenticação, como assinaturas digitais e troca de chaves.

### Pré-requisitos
OpenSSL
#### Linux: 
Geralmente já vem instalado por padrão. Use o comando openssl no terminal para verificar.
#### macOS: 

Instale via Homebrew: brew install openssl@1.1
#### Windows: 
Incluído na instalação do Git para Windows. E pode ser executado no terminal GIT BASH

### Gerando a Chave Privada ECDSA
```Bash
openssl genpkey -algorithm RSA -out priv-arcs.pem
```
#### ecparam: 
Geração de chave por curva elíptica com parâmetros.
#### -name secp256k1: 
Utiliza a curva elíptica secp256k1, amplamente utilizada em criptomoedas como Bitcoin.
#### -genkey: 
Gera a chave privada.
#### -noout: 
Impede a saída de informações adicionais na chave.
#### -out priv-arcs.pem: 
Salva a chave em um arquivo chamado priv-arcs.pem.
### Gerando a Chave Pública ECDSA a partir da Privada
```sh
openssl rsa -in priv-arcs.pem -pubout -out pub-arcs.pem
```
#### ec: 
Opera em curvas elípticas.
#### -in priv-arcs.pem: 
Lê a chave privada gerada anteriormente.
#### -pubout: 
Gera a chave pública.
#### pub-arcs.pem: 
Salva a chave pública em um arquivo chamado pub-arcs.pem.

### Verificando as Chaves
Para visualizar o conteúdo das chaves, utilize o comando cat:

```sh
cat priv-arcs.pem
cat pub-arcs.pem
```

Armazenamento Seguro
Chave Privada: Mantenha a chave privada em local seguro e confidencial. Ela é essencial para assinar digitalmente dados e descriptografar informações.

Chave Pública: A chave pública pode ser compartilhada livremente. Ela é utilizada para verificar assinaturas digitais e criptografar dados que somente o detentor da chave privada pode descriptografar.

Utilizando as Chaves:
As chaves geradas podem ser utilizadas em diversas aplicações, como:

Assinaturas digitais: Garantir a autenticidade e integridade de documentos.

Criptografia: Criptografar dados para proteger a confidencialidade.

Autenticação: Verificar a identidade de usuários em sistemas.

### Observações:

Algoritmo: A curva elíptica secp256k1 é uma escolha comum devido à sua segurança e eficiência.

Formato: As chaves são salvas no formato PEM, um formato padrão para armazenar certificados e chaves criptográficas.

Segurança: É fundamental proteger a chave privada. Evite compartilhá-la e armazene-a em um local seguro.

Para mais informações:
Consulte a documentação oficial do OpenSSL para detalhes sobre outros algoritmos, opções e funcionalidades.

## Para ambiente de Homologação ou Produção utilize o Azure Key Vaults
> Este guia tem como objetivo fornecer uma introdução básica à geração de chaves ECDSA utilizando o OpenSSL. SOMENTE para o ambiente de desenvolvimento, JAMAIS essa chave deve ser utilizada em ambiente de homologação ou produção

