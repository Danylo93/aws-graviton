# Lab DevOps: AWS Graviton + GitLab CI

Neste GitHub, o lab fica na raiz da branch `master`. Para executar a pipeline, envie este projeto ao GitLab mantendo a branch `master`; o GitHub hospeda o código.

Aplicação Go pequena para acompanhar o caminho **código → teste → compilação ARM64 → imagem de contêiner ARM64 → deploy manual → health check → rollback**. O laboratório local é o ponto de partida; a parte AWS só é criada após você conferir o plano e os custos na sua conta.

## Primeiro: o que é Graviton?

**AWS Graviton** é a família de processadores Arm da AWS. Uma `t4g.small` usa **Graviton2** e executa sistema operacional e imagens `arm64/aarch64`. Um binário `amd64/x86_64` feito para seu notebook comum não roda nativamente nela. Por isso este lab compila Go com `GOARCH=arm64`, constrói uma imagem `linux/arm64` e confere a arquitetura no CI e no servidor.

`GOARCH=arm64` é a arquitetura de compilação do Go; `aarch64` é como o Linux costuma nomeá-la; `linux/arm64` é a plataforma da imagem OCI. **Cross compilation** gera o binário ARM64 num runner x86. A imagem usa `scratch`, sem etapas `RUN`, para dispensar emulação QEMU. A execução final na EC2 é nativa.

## Custo: leia antes de usar a AWS

- **Sem AWS:** `scripts/local.sh` e os jobs de CI não criam recursos na sua conta. O GitLab.com e seus runners têm limites próprios; confira seu plano de minutos e armazenamento.
- **Com AWS:** a AWS anuncia teste de **até 750 h/mês de `t4g.small` até 31/12/2026**, sujeito às condições da oferta. Isso cobre a instância dentro da franquia, **não todos os recursos**. O exemplo usa IPv4 público, disco gp3 de 8 GiB, armazenamento de state local e tráfego. IPv4 público tem tarifa publicada de **US$ 0,005/h** fora de benefícios/créditos aplicáveis; disco e tráfego podem gerar consumo também. Mesmo uma instância parada conserva o disco. A instância usa modo de créditos CPU `standard` para evitar cobrança de excedentes `unlimited`.
- Se sua conta foi criada no **AWS Free plan** novo, a AWS indica créditos iniciais e encerramento quando o período/crédito acabar, sem cobrança a menos que você migre para plano pago. Contas antigas ou no **Paid plan** seguem condições diferentes. **Não é possível prometer custo zero universal.** Para custo efetivamente zero, fique na etapa local; faça a etapa AWS apenas se confirmar cobertura ou aceitar consumo dos seus créditos. Configure alerta de orçamento na sua conta e destrua a infraestrutura ao terminar. Alertas não são travas de cobrança.
- O laboratório **não usa** EKS, ECS/Fargate, NAT Gateway, ALB, ECR ou banco de dados. Uma VM pequena basta para demonstrar o fluxo.

Documentação oficial: [T4g](https://aws.amazon.com/ec2/instance-types/t4/), [Free Tier](https://aws.amazon.com/free/), [preço IPv4](https://aws.amazon.com/vpc/pricing/), [créditos de CPU](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances-unlimited-mode.html), [GitLab CI](https://docs.gitlab.com/ci/), [GitLab Runner](https://docs.gitlab.com/runner/).

## Pré-requisitos

- Local/WSL Ubuntu: Go 1.22+, Docker Engine e acesso a um projeto GitLab (GitLab.com funciona). Terraform e AWS CLI só são necessários para a etapa AWS. `file` é opcional.
- Runner compartilhado GitLab para teste/build (Docker-in-Docker requer runner que aceite `docker:dind`); um **runner próprio no WSL** com executor `shell`, tag `local-deploy`, habilitado para jobs protegidos, para deploy. Ele precisa ter `ssh` e `scp` e ficar ligado na hora do job. Cadastre o runner pela interface **Settings > CI/CD > Runners** e siga o comando de registro fornecido pelo GitLab. Use runner de projeto, com `Run untagged jobs` desativado. Proteja `master` e limite quem pode disparar o deploy manual.
- AWS CLI configurado com usuário/role autorizado para criar e apagar EC2, security group e key pair. **Não coloque credenciais AWS no GitLab**; Terraform roda no seu WSL. Tenha VPC default e pelo menos uma subnet default na região.

## Fase 1: local (sem conta AWS)

```bash
./scripts/local.sh
# opcional: se seu Docker tiver emulação ARM64 configurada
# docker run --rm --platform linux/arm64 -p 127.0.0.1:8080:8080 graviton-lab:local
# curl http://127.0.0.1:8080/
```

Observe `go test`, `file bin/server` e `docker image inspect graviton-lab:local --format '{{.Architecture}}'`. A execução de uma imagem ARM64 no PC x86 requer emulação; a compilação e construção da imagem aqui **não** requerem.

## Fase 2: pipeline GitLab

Workflow mínimo com três jobs: teste + compilação → imagem → deploy manual. O arquivo `.gitlab-ci.yml` deve ficar na raiz do projeto GitLab.

Crie um projeto privado GitLab e envie esta pasta como repositório. Merge requests e commits em `master` executam teste, `go vet`, compilação `arm64` e build da imagem OCI `arm64`. O build salva um `tar.gz` como **artifact do GitLab por 1 dia**; não usa registry pago. Apenas push na branch `master` oferece `deploy_aws` manual. MR não faz deploy. A etapa de imagem exige runner compartilhado compatível com Docker-in-Docker; se sua instância GitLab não permitir, use um runner próprio Docker com `privileged` habilitado apenas para jobs de build de projeto confiável.

| Job | O que comprova | Saída |
| --- | --- | --- |
| `test_compile_arm64` | Testes, análise estática Go e binário ELF AArch64 | `bin/server` |
| `build_arm64_image` | Imagem OCI `linux/arm64` | artifact `tar.gz` |
| `deploy_aws` | Instala imagem na T4g e verifica `/health` | serviço ou rollback |

## Fase 3: AWS (opcional, com gate de custo)

1. Confirme Free Tier/créditos e cotas na conta; escolha `us-east-1` se houver `t4g.small` disponível. Confira custos de EBS, IPv4 e saída de dados. Configure um alerta em Billing antes de provisionar. Nada nesta pasta executa `terraform apply` automaticamente.
2. No WSL, crie chave específica para o lab: `ssh-keygen -t ed25519 -f ~/.ssh/graviton_lab -C graviton-lab`. Nunca versione a chave privada. Descubra **seu IPv4 público do local onde roda o runner** e informe `IP/32` em `ssh_cidr`. Se o IP mudar, atualize `terraform.tfvars` e aplique de novo.
3. Copie `infra/terraform.tfvars.example` para `infra/terraform.tfvars`; troque `ssh_cidr`, ajuste região se necessário. Este arquivo é local e deve ficar fora do git (veja `.gitignore`).
4. Provisione manualmente:

```bash
cd infra
terraform init
terraform plan -out=lab.tfplan
terraform apply lab.tfplan
terraform output public_ip
```

5. Aguarde o cloud-init terminar: `ssh -i ~/.ssh/graviton_lab ec2-user@IP 'cloud-init status --wait; uname -m; docker --version'`. Esperado: `aarch64`. A porta 8080 não é pública; teste por túnel: `ssh -i ~/.ssh/graviton_lab -L 8080:127.0.0.1:8080 ec2-user@IP` e, em outro terminal, `curl http://127.0.0.1:8080/`.
6. **Verifique a chave de host SSH pela console/serial da EC2 ou outro canal confiável antes de confiar nela.** Grave a linha verificada em uma variável GitLab `SSH_KNOWN_HOSTS` (tipo Variable). Não use `StrictHostKeyChecking=no`.
7. Em GitLab **Settings > CI/CD > Variables**, crie `SSH_PRIVATE_KEY` como variável **File**, **Protected** (conteúdo completo da chave privada, com newline final); crie `EC2_HOST` e `SSH_KNOWN_HOSTS` também protegidas. A variável File torna `SSH_PRIVATE_KEY` o caminho temporário da chave no job. Não versione `terraform.tfstate`, chaves ou outputs sensíveis.
8. Envie commit para `master`, espere jobs verdes, dispare `deploy_aws` manualmente. O runner local precisa ter conectividade com a instância e pertencer ao CIDR autorizado. Inspecione o log do job e teste o endpoint por túnel. Endpoint `/` mostra `architecture: arm64` e `version: SHA`; `/health` mostra `status: ok`.
9. Faça uma mudança em `message`, repita a pipeline e observe a nova versão. Para treinar rollback, quebre a aplicação **depois da compilação** de modo que não responda `/health` (por exemplo, altere a rota) e veja o script restaurar a imagem anterior. Depois reverta o commit. O rollback depende de haver um deploy anterior bem sucedido.

## Desligar e limpar

```bash
cd infra
terraform destroy
```

Confirme no console que não sobraram a instância, o volume, o security group e o par de chaves. O `terraform destroy` requer o **mesmo arquivo `terraform.tfstate` local**; não o apague antes da limpeza. Desligar (`stop`) não remove disco. Apague artifacts de pipeline se quiser reduzir armazenamento GitLab. Remova o runner e as variáveis protegidas quando concluir o estudo.

## Glossário e dúvidas frequentes

| Termo | Explicação neste lab |
| --- | --- |
| Graviton2 / T4g | Processador Arm AWS / família EC2 de uso geral que o utiliza. `t4g.small` é o tamanho escolhido. |
| ARM64 x AMD64 | Arquiteturas de CPU diferentes; o executável e a imagem devem corresponder à máquina de destino. |
| AMI | Imagem do sistema operacional EC2. O Terraform busca a Amazon Linux 2023 ARM64 atual via Parameter Store. |
| EC2 / EBS | Máquina virtual / disco persistente separado; ambos podem consumir franquia ou créditos. |
| VPC / subnet / security group | Rede virtual / segmento de rede / firewall de entrada e saída. SSH fica restrito ao IP `/32`. |
| IaC / Terraform state | Infra como código / arquivo que guarda os recursos geridos; proteja o state e mantenha-o para destruição. |
| CI / CD | Integração contínua testa e empacota; entrega contínua aqui é um deploy manual controlado. |
| Runner / job / stage | Agente de execução / tarefa / fase da pipeline. O runner local só roda deploy. |
| Artifact / image | Arquivo temporário passado entre jobs / pacote OCI executado pelo Docker. |
| Health check / rollback | Teste da rota `/health` / retorno à imagem anterior em caso de falha após deploy. |
| Créditos CPU `standard` | Permite burst até os créditos disponíveis, sem a cobrança extra do modo `unlimited`; o desempenho pode reduzir ao esgotar créditos. |

### Exercícios

1. Compare `go env GOARCH`, `file bin/server`, `docker image inspect` e `uname -m` no destino; explique a diferença entre host x86, binário Arm e processador Graviton.
2. Crie MR com teste falhando; confirme que não existe deploy. Corrija e faça merge.
3. Implante duas versões e provoque health check ruim na terceira; confirme que a segunda volta.
4. Faça `terraform plan` após trocar CIDR e veja somente a regra de rede mudar; finalize com `terraform destroy`.

**Limites:** um único host, sem TLS público, sem alta disponibilidade, sem secrets de aplicação, sem registry remoto. É um laboratório para aprender arquitetura e pipeline, não um modelo pronto para produção.
