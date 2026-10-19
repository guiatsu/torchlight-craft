# AGENTS.md — Torchlight Craft Planner

> Instruções para agentes de programação operando neste repositório. Leia antes de modificar código.

## Produto e escopo vigente

- Projeto: **Torchlight Craft Planner**, aplicativo desktop Windows para edição de equipamentos de Torchlight: Infinite.
- Stack: **Python 3.12+, PySide6, Qt Quick/QML, dataclasses, catálogo local SQLite e biblioteca JSON local**. Build Windows com `pyside6-deploy`/Nuitka.
- **Marco atual: v0.2.0 — importação exaustiva e auditável do catálogo comunitário TLIDB, com busca integrada ao editor.** Não adicionar crafting aleatório, probabilidade, custos, otimização, OCR, integração com o jogo ou atualização remota automática.
- A tela de crafting do jogo é referência de **composição e fluxo visual**, não apenas de paleta. O app continua sendo um *editor*, não uma réplica funcional do crafting nesta versão.
- A captura do catálogo de 2026-10-19 contém 49 categorias, 2.194 bases, 642 famílias de afixos, 13.303 tiers e 831 registros de outras tabelas. Os dados comunitários **não estão confirmados para SS14**. A auditoria está parcial; nunca apresente regras estimadas como oficiais.

## Estado do repositório na criação deste arquivo (2026-10-19)

- `core/controller.py` reúne cerca de **850 linhas**, misturando ponte Qt/QML, estado do editor, seleção de catálogo, operações de biblioteca e mensagens.
- `core/models.py` concentra entidades de equipamento, base, afixo, tier e enums.
- `ui/Main.qml`, `ui/ItemEditor.qml` e `ui/components/AffixSelector.qml` contêm layout e estilos muito grandes.
- `services/item_repository.py` mantém a biblioteca em JSON com `schema_version=1`, gravação atômica e backup `.bak`.
- `data/{bases,affixes,sources}.json` mantém os dados legados usados como compatibilidade; `data/catalog.sqlite3` é o catálogo normalizado da v0.2.
- O CI Windows já compilou com Nuitka, mas a execução empacotada falhou no smoke test (`--smoke-test`). **Não remover nem ignorar essa verificação para obter CI verde.**
- Consulte sempre a branch/commit atual; estes fatos são um diagnóstico inicial, não substituem reavaliação.

## Atualização da implementação v0.2.0

- A composição Qt está em `app/controller.py`; `core/controller.py` permanece apenas como import de compatibilidade.
- `app/viewmodels/` contém os view-models do equipamento, navegação de afixos e biblioteca. Eles compartilham um único `ItemEditorService` e uma única sessão mutável.
- `core/models/` separa equipamento, base e afixos; `core.models` reexporta os nomes públicos anteriores. `schema_version=1` e os campos gravados permanecem iguais.
- `services/` contém casos de uso sem PySide6 para edição, busca/seleção de afixos e operações da biblioteca.
- Slots explícitos só são renderizados para limites presentes no catálogo; `visual_example_only` continua identificado como provisório. Bases com limite desconhecido não recebem slots vazios inventados.
- Incompatibilidades resultantes de troca de base são mantidas, listadas e bloqueiam salvar. A interface oferece substituição individual ou remoção em lote com confirmação.
- O workflow Windows usa `tools/stage_windows_runtime.ps1` e captura o código de saída com `Start-Process -Wait -PassThru`. O executável grava falhas de inicialização em `%TEMP%\TorchlightCraftPlanner-startup.log`; o smoke test continua obrigatório.
- A validação offscreen confirma inicialização QML, mas não substitui revisão visual no Windows.
- `data/catalog.sqlite3` é o catálogo local normalizado (schema v2); a biblioteca de equipamentos do usuário continua em JSON `schema_version=1`. O app não consulta a rede na inicialização.
- `tools/tlidb/` descobre categorias dinamicamente, respeita `robots.txt`, usa cache com hash e requisições serializadas, importa offline, valida e compara snapshots. Não mova o importador para o caminho de inicialização do aplicativo.
- Os relatórios em `reports/` registram descoberta, retenção, erros, campos ausentes e validação. A captura atual reteve 100% dos registros encontrados, mas 1.219 classificações e 50 campos continuam sem confirmação suficiente; status geral `partial` é intencional.
- Base ou afixo sem classificação conhecida permanece pesquisável e rotulado, mas não entra silenciosamente na seleção de craft padrão. Não inferir `non_craftable` a partir de ausência de dados.
- Correções manuais verificadas devem ficar em uma camada explícita com proveniência; antes de reaplicar uma captura, detectar e reportar conflitos. Nunca editar o SQLite gerado como única cópia de uma correção.

## Princípios obrigatórios

1. **Refatorar por comportamento preservado.** Antes de mover módulos, caracterize o fluxo existente com testes; mova uma responsabilidade de cada vez e execute os testes depois.
2. **Uma fonte de verdade.** Estado editável de equipamento deve existir em um único modelo/serviço de sessão; QML e view-models não devem manter cópias independentes que possam divergir.
3. **Domínio não depende de Qt.** Entidades, validações e futuras regras de craft devem ser Python puro, testáveis sem interface gráfica.
4. **QML não contém regras de negócio.** QML trata layout, interações e apresentação; filtros, elegibilidade, validação e persistência ficam fora dele.
5. **Controllers não viram arquivos-depósito.** Não acrescentar novas funcionalidades ao controller monolítico; extrair por responsabilidades e manter apenas a ponte de apresentação necessária.
6. **Sem arquitetura excessiva.** Não introduzir DI frameworks, mediators, microserviços, backend web, banco remoto ou abstrações genéricas sem uso real.
7. **Compatibilidade de dados primeiro.** Preservar itens salvos, IDs existentes, comportamento de backups e esquema v1; qualquer migração futura precisa ser explícita, testada e recuperável.
8. **Dados auditáveis.** Todo dado de jogo não óbvio deve possuir origem, hash/ref de origem quando disponível e status de verificação. Preservar pesos exatos, inclusive zero; não transformá-los em probabilidades nem fabricar pesos, tiers, conflitos, requisitos ou limites de slots.
9. **Importação exaustiva e retenção.** Comparar páginas descobertas com inventário de controle, nunca omitir categorias/tabelas silenciosamente e manter registros desconhecidos em relatórios ou armazenamento bruto. Retenção de registro não equivale a cobertura de regras.
10. **Sem assets não autorizados.** Usar os vetores originais do projeto ou assets com licença adequada; a imagem do jogo serve como referência visual.
11. **Não mascarar falhas.** Não suprimir exceções, testes, warnings do QML, erros de build nem marcar tarefas como verificadas sem execução real.

## Organização-alvo (guia, não licença para reescrever tudo)

```text
main.py                     # composição e inicialização, sem regras de negócio
app/
  controller.py             # fachada Qt/QML fina, se necessária à compatibilidade
  viewmodels/
    item_editor.py          # estado/ações expostos à UI
    affix_browser.py        # busca, seleção e filtros do catálogo
    library.py              # operações/estado da biblioteca na UI
core/
  models/
    equipment.py            # EquipmentItem, AffixInstance
    affix.py                # AffixDefinition, TierOption, enums
    base.py                 # BaseDefinition
  catalog.py                # leitura e validação estrutural dos dados locais
  validation.py             # validação de domínio
  serialization.py          # formato de itens; compatibilidade schema v1
services/
  item_editor_service.py    # casos de uso de edição, sem Qt
  item_library_service.py   # coordenação de salvar/abrir/duplicar/excluir
  item_repository.py       # armazenamento JSON, atomicidade e backups
ui/
  Main.qml                  # composição da janela, sem milhares de linhas
  ItemEditor.qml            # layout da tela do editor
  components/               # componentes reutilizáveis de propósito claro
  theme/                    # tokens centralizados de cor, texto e espaçamento
assets/                     # ícones/arte própria
data/                       # bases/afixos/fontes com proveniência
  catalog.sqlite3           # catálogo TLIDB normalizado, schema v2
tools/tlidb/                # descoberta, importação, validação e diff offline
reports/                    # cobertura, unresolved, errors e validação da captura
tests/                      # testes de domínio, integração e smoke
.github/workflows/          # CI Windows e validação de build
```

Esta é uma **direção arquitetural**. Preserve imports públicos onde possível ou introduza adaptadores temporários. Não duplique `EquipmentItem`/`AffixInstance` em `app` e `core`. Evite deixar arquivos vazios ou wrappers sem função apenas para cumprir a árvore. `app/viewmodels` podem ser QObjects; `core` e `services` não devem importar PySide6, salvo justificativa pontual documentada.

## Responsabilidades e limites

- **`core/models/`**: tipos e invariantes das entidades. Um módulo para equipamento/instância e outro para catálogo (bases, definições e tiers). Tipos de domínio não armazenam sinais Qt.
- **`core/catalog.py`**: carrega o SQLite local e adaptadores JSON legados; valida referências e formatos sem conhecimento de widgets.
- **`core/validation.py`**: erros tipados ou mensagens claras, sem notificações visuais nem efeitos colaterais.
- **`services/`**: editar item, trocar base, incluir/substituir/remover afixo, persistir e gerenciar biblioteca; funções e serviços testáveis sem QML.
- **`app/`**: integração Qt, propriedades/sinais/slots, seleção e transformação de dados para a apresentação. Preferir controladores pequenos e específicos a uma classe que manipule tudo.
- **`ui/`**: componentes pequenos, slots visuais explicitamente desenhados, estados de foco/seleção/desabilitado, layouts e tokens centralizados. Não copiar regras de tier ou nível para QML.
- **`data/`**: catálogo SQLite normalizado e dados legados com proveniência e status; alterar o catálogo não deve exigir modificar QML. Catálogo de jogo e biblioteca pessoal permanecem separados.
- **`tools/tlidb/`**: ferramenta de desenvolvimento, nunca chamada no startup; descoberta dinâmica, cache, importador, validação, relatório e diff. Não contornar `robots.txt`, limites de requisição ou hashes de origem.
- **`reports/`**: evidência da captura. Conservar classificações unknown, fontes sem campos e divergências; partial não deve ser convertido em sucesso completo.
- **`tests/`**: testes de comportamento e regressão do editor, biblioteca, importação, parsers, armazenamento e compatibilidade do catálogo.

## Trabalho visual: critérios do editor

A referência principal é a **screenshot de crafting do Torchlight: Infinite fornecida pelo usuário**. Se não estiver disponível no contexto do agente, solicite o arquivo antes de afirmar fidelidade visual; siga estas regras enquanto isso:

- Layout **compacto e centralizado**, com painel do item à esquerda e possíveis afixos à direita; fundo envolvente, evitando duas colunas enormes que ocupem cada pixel da janela.
- **Item e afixos devem ser o foco inicial**. Seletor de categoria/base, Item Level e Priceless ficam em uma barra ou painel compacto, sem dominar a tela.
- Representar explicitamente cada **slot ocupado e vazio** de Prefix/Suffix, com ordem, seleção e feedback visual. Quantidades e restrições seguem o catálogo; quando desconhecidas, não fingir que são regras oficiais.
- Ícone/identidade do item, nome, tier e texto de afixo precisam de hierarquia legível. Distinguir Basic/Advanced/Ultimate sem depender somente de cor.
- Selecionar um slot deve contextualizar o painel direito; editar tier/valor deve ocorrer **próximo ao item/afixo selecionado**, não no rodapé remoto de uma lista quase vazia.
- Suportar 1920×1080 e janela menor respeitando tamanhos mínimos e áreas com rolagem. Reduzir espaço vazio *não funcional* e fontes microscópicas.
- Avisos de 'dados não confirmados' devem ser visíveis e acessíveis, mas não repetidos em cada região principal; fonte detalhada em tooltip/painel secundário.
- Estilização centralizada: não repetir dezenas de cores hexadecimais, margens e tamanhos sem motivo em cada QML.
- Manter os fluxos v0.1: novo, editar, adicionar, substituir, remover, salvar, carregar, renomear, duplicar, excluir e confirmar alterações não salvas.
- **Sem botão 'Craft', custos, sorteios ou simulações nesta versão.**

## Ordem recomendada de intervenção

1. Ler `README.md`, `PRODUCT.md`, catálogo, modelos, controlador, QML e testes; registrar diagnóstico breve e status de CI.
2. Criar testes de caracterização para os fluxos existentes, especialmente mudança de base, seleção/edição de afixo, validação e descarte de alterações.
3. Separar `core/models.py` por responsabilidade com compatibilidade de imports e round-trip da serialização v1.
4. Extrair do `core/controller.py` primeiro operações puras, depois operações de biblioteca/catálogo; manter uma fachada Qt fina enquanto QML migra gradualmente.
5. Dividir componentes QML e extrair tokens de tema; refinar o layout seguindo a screenshot e conferir em execução real.
6. Diagnosticar e corrigir o empacotamento/smoke Windows; incluir saída diagnóstica no CI, sem remover o teste. O build atual inclui dados desnecessários: limitar inclusões a QML/assets/catálogo requeridos.
7. Atualizar testes, documentação e comandos de build; entregar relatório honesto do que foi e não foi validado.

**Não realizar uma migração massiva e a reformulação visual na mesma alteração indivisível.** Faça checkpoints verificáveis e pequenos commits quando o fluxo de trabalho permitir.

## Persistência e migração

- `schema_version=1` é contrato público para itens já salvos; não alterar formato à força para viabilizar refactor.
- Preservar `id`, `base_id`, `item_level`, `priceless`, `rarity` e `affixes`/seus campos existentes.
- Repositório continua salvando atomicamente e mantém backup quando sobrescreve biblioteca existente.
- Não apagar nem corrigir automaticamente itens antigos que contenham dados desconhecidos; exibir erro/estado de incompatibilidade de forma recuperável.
- Criar teste de carga do JSON v1 antes de mudar arquivos de modelos.

## Testes e execução

Windows PowerShell com `.venv` já criada:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe main.py --smoke-test
.\.venv\Scripts\pyside6-deploy.exe --mode standalone
```

Linux/WSL com ambiente virtual já criado:

```bash
.venv/bin/python -m pytest
QT_QPA_PLATFORM=offscreen .venv/bin/python main.py --smoke-test
```

Não presumir que o smoke `offscreen` substitua revisão visual num Windows real. Antes de instalar dependências ou elevar privilégios, inspecionar o ambiente e pedir autorização. As bibliotecas devem vir de fontes oficiais, sem scripts remotos encadeados ou desabilitação de proteções.

CI: testes Python + inicialização QML + build Nuitka + smoke do executável empacotado + artifact somente depois de sucesso. Se `--windows-console-mode=disable` ocultar erros, registrar diagnóstico em arquivo temporário ou habilitar console **apenas no build de depuração do CI**. Não converter uma falha real em sucesso silencioso.

## Definição de concluído

- Projeto abre e edita itens sem regressão.
- Fluxos existentes funcionam e persistência v1 é preservada.
- Controller e modelos estão separados por responsabilidade, com dependências dirigidas para o domínio.
- Interface se aproxima **estruturalmente** da screenshot e apresenta slots individuais, hierarquia clara e controles contextuais.
- Testes passam; problemas de empacotamento são diagnosticados e corrigidos ou documentados com evidência, nunca ignorados.
- `README.md` e `PRODUCT.md` refletem apenas capacidades reais.
- O agente informa arquivos alterados, testes executados, limitações e passos ainda pendentes; não afirma ter realizado testes visuais sem acesso à GUI.

## Condutas proibidas

- Manter o escopo atual focado em edição e catálogo offline; não acrescentar crafting, simulação ou atualização automática remota.
- Não trocar PySide6/QML por outra stack sem decisão explícita.
- Não apagar dados locais, zerar bibliotecas, alterar esquema v1 silenciosamente ou forçar exclusão de afixos existentes.
- Não inventar dados do jogo, probabilidades ou licenças de assets.
- Não adicionar bibliotecas de UI concorrentes, serviços online ou infraestrutura não necessária.
- Não ocultar falhas no CI ou remover testes para passar o build.
