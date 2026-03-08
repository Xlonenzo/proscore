---
name: uiux-master
description: >
  Motor de design UI/UX de nível sênior. Use SEMPRE que o usuário pedir para criar,
  redesenhar, melhorar ou avaliar qualquer interface — web, mobile, dashboard, landing page,
  componente, app, SaaS, e-commerce, portfólio, ou qualquer produto digital. Também dispara
  quando o usuário mencionar "interface bonita", "design moderno", "referências visuais",
  "Behance", "UI/UX", "melhores práticas de design", "redesign", "look and feel",
  "identidade visual", "experiência do usuário", ou quando enviar código/screenshot e
  pedir para melhorar visualmente. OBRIGATÓRIO: a skill lê a aplicação existente,
  busca PELO MENOS 3 referências reais no Behance, aplica conceitos atuais de UI/UX
  dos melhores designers de 2025/2026, e só então cria ou refatora o código.
---

# UI/UX Master Skill

Produz interfaces de nível award-winning: lê a aplicação, pesquisa referências reais,
aplica os princípios dos melhores designers do mundo em 2025/2026, e entrega código
que parece obra de um designer sênior — nunca "gerado por IA".

---

## PROCESSO OBRIGATÓRIO (execute SEMPRE nesta ordem)

---

### FASE 0 — Ler a Aplicação Existente

**Antes de qualquer pesquisa ou código**, entenda o que já existe:

```
Se o usuário enviou arquivos/código:
  → Leia TODO o código com a tool `view` ou lendo o conteúdo
  → Identifique: stack, componentes, fluxo, dados, estado
  → Mapeie problemas visuais: espaçamento, hierarquia, cores, tipografia
  → Anote o que DEVE ser preservado (funcionalidade, dados, lógica)

Se o usuário descreveu uma aplicação sem enviar código:
  → Pergunte: "Você tem código ou screenshot existente? Se sim, compartilhe."
  → Se não houver nada ainda, vá para FASE 1 como projeto novo

Se for projeto novo do zero:
  → Extraia do pedido: propósito, público, tom, constraints técnicos
```

**Declare o que você entendeu** antes de continuar. Exemplo:
> "Li o código. É um dashboard React com 3 componentes principais.
> Problemas identificados: hierarquia visual fraca, espaçamento inconsistente,
> sem sistema de cores definido. Vou preservar a lógica de estado e os dados."

---

### FASE 1 — Pesquisar os Melhores Designers de 2025/2026

Use `web_search` para buscar quem está dominando o design agora:

```
# Busca 1 — Tendências e premiados do ano
"best UI UX designers 2025" OR "awwwards winners 2025 web design"

# Busca 2 — Trabalhos em destaque no Behance
"Behance top UI design 2025" OR "best interface design projects 2025"

# Busca 3 — Tendências específicas ao setor do projeto
"[setor] UI design trends 2025" (ex: "SaaS dashboard design trends 2025")
```

**Extraia e documente:**
- 2-3 nomes de designers/estúdios em destaque (com estilo característico)
- 3-5 tendências visuais dominantes no segmento
- Padrões de interação premiados (motion, micro-interactions, navegação)

Mencione ao usuário: *"Os designers de referência para este projeto são X e Y,
cujo trabalho aparece em [fonte]. As tendências dominantes são..."*

---

### FASE 2 — Buscar PELO MENOS 3 Referências Reais no Behance

**Obrigatório: abra e leia pelo menos 3 projetos Behance relevantes.**

#### Passo 2.1 — Buscar projetos
```
# Query primária (adapte ao setor)
site:behance.net [tipo-de-interface] UI design 2024 2025

# Query de estilo específico
site:behance.net [setor/tema] interface design minimal/bold/dark

# Query de premiados
site:behance.net award winning [categoria] UI design
```

Use `references/behance-queries.md` para queries prontas por setor.

#### Passo 2.2 — Abrir e ler os projetos (OBRIGATÓRIO)
Para cada projeto encontrado, use `web_fetch` na URL do Behance:

```javascript
// Fetch de cada projeto
web_fetch("https://www.behance.net/gallery/[ID]/[nome-projeto]")
```

**O que extrair de cada referência:**
```
REFERÊNCIA 1: [URL]
- Paleta dominante: [hex codes se visíveis, ou descrição]
- Tipografia: [família, pesos, hierarquia]
- Layout: [grid, assimetria, proporções]
- Componentes notáveis: [cards, nav, hero, forms]
- Micro-interações: [hover, transitions, loading]
- Espaçamento: [generoso/apertado, ritmo vertical]
- O que torna único: [elemento de diferenciação]

REFERÊNCIA 2: [URL] — mesma estrutura
REFERÊNCIA 3: [URL] — mesma estrutura
```

#### Passo 2.3 — Síntese das Referências
Antes de codificar, apresente ao usuário:
> "Estudei 3 projetos no Behance. A síntese visual que vou aplicar:
> **Paleta**: [...] inspirada em [ref1].
> **Tipografia**: [...] como visto em [ref2].
> **Layout**: [...] extraído de [ref3].
> **Diferencial**: [elemento único que vou incorporar]."

---

### FASE 3 — Conceitos de UI/UX Aplicados (2025/2026)

Antes de codificar, escolha e declare quais princípios se aplicam ao projeto.
Leia `references/uiux-principles.md` para o guia completo. Resumo dos principais:

#### Princípios Estruturais
- **Visual Hierarchy**: O olho deve seguir um caminho claro. F-pattern ou Z-pattern.
- **8pt Grid System**: Todos os espaçamentos múltiplos de 8 (8, 16, 24, 32, 40, 48...)
- **Gestalt**: Proximidade, semelhança, continuidade e fechamento no layout
- **Progressive Disclosure**: Mostre só o necessário; detalhe sob demanda

#### Tendências Dominantes 2025/2026
- **Spatial Design**: Profundidade, sombras sutis, layers sobrepostos (estilo visionOS)
- **Glassmorphism refinado**: `backdrop-filter: blur()` com opacidade bem calibrada
- **Bento Grid**: Células de tamanhos variados como Apple Marketing Pages
- **Typographic Hero**: Título gigante como elemento visual principal
- **Dot/Noise Texture**: Textura sutil para profundidade sem peso visual
- **Semantic Color Tokens**: Cores com significado, não apenas estética
- **Motion com propósito**: Animações que comunicam estado, não decoram
- **Dark mode first**: Interface dark como padrão premium, light como variante

#### Anti-patterns a EVITAR
- Gradiente roxo genérico em fundo branco
- Layout de 2 colunas simétricas sem propósito
- Fonte padrão (Inter, Roboto) sem personalidade
- Sombras `box-shadow: 0 2px 4px rgba(0,0,0,0.1)` genéricas
- Botões `border-radius: 4px` sem sistema definido
- Cards todos iguais sem hierarquia visual
- Hero com stock photo atrás de texto
- "Features section" com 3 ícones iguais e texto genérico

---

### FASE 4 — Sistema de Design (antes do código)

**Defina o sistema ANTES de escrever qualquer JSX/HTML:**

```css
/* 1. Tokens de cor semânticos */
:root {
  /* Backgrounds */
  --color-bg-base:       [cor base];
  --color-bg-surface:    [superfícies elevadas];
  --color-bg-overlay:    [modais, tooltips];

  /* Bordas */
  --color-border-subtle: [rgba muito sutil];
  --color-border-default:[padrão];
  --color-border-strong: [emphasis];

  /* Interativo */
  --color-accent-default:[cor principal de ação];
  --color-accent-hover:  [hover state];
  --color-accent-muted:  [backgrounds de accent 10%];

  /* Texto */
  --color-text-primary:  [leitura principal];
  --color-text-secondary:[hierarquia 2];
  --color-text-muted:    [labels, placeholders];
  --color-text-inverse:  [texto em fundo escuro/claro];

  /* Status */
  --color-success: #22C55E;
  --color-warning: #F59E0B;
  --color-error:   #EF4444;
  --color-info:    #3B82F6;

  /* Tipografia */
  --font-display:  '[Fonte Display]', sans-serif;
  --font-body:     '[Fonte Body]', sans-serif;
  --font-mono:     '[Fonte Mono]', monospace;

  /* Escala tipográfica */
  --text-xs:   0.75rem;   /* 12px */
  --text-sm:   0.875rem;  /* 14px */
  --text-base: 1rem;      /* 16px */
  --text-lg:   1.125rem;  /* 18px */
  --text-xl:   1.25rem;   /* 20px */
  --text-2xl:  1.5rem;    /* 24px */
  --text-3xl:  1.875rem;  /* 30px */
  --text-4xl:  2.25rem;   /* 36px */
  --text-5xl:  3rem;      /* 48px */
  --text-6xl:  3.75rem;   /* 60px */
  --text-7xl:  4.5rem;    /* 72px */

  /* Espaçamento (8pt grid) */
  --space-1: 8px;   --space-2: 16px;  --space-3: 24px;
  --space-4: 32px;  --space-5: 40px;  --space-6: 48px;
  --space-8: 64px;  --space-10: 80px; --space-12: 96px;
  --space-16: 128px;--space-20: 160px;--space-24: 192px;

  /* Raios */
  --radius-xs: 4px;   --radius-sm: 8px;
  --radius-md: 12px;  --radius-lg: 16px;
  --radius-xl: 20px;  --radius-2xl: 28px;
  --radius-full: 9999px;

  /* Motion */
  --ease-out:    cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-in-out: cubic-bezier(0.45, 0, 0.55, 1);
  --duration-fast: 120ms;
  --duration-base: 200ms;
  --duration-slow: 350ms;
  --duration-page: 600ms;
}
```

---

### FASE 5 — Tipografia Premium

**Regra absoluta: nunca use Inter, Roboto, Arial como fonte principal.**

Consulte `references/typography-pairs.md` para combinações. Rápidas:

```html
<!-- TECH MODERN (SaaS, DevTools, AI) -->
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<!-- EDITORIAL LUXURY (Fashion, Finance Premium, Brand) -->
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">

<!-- BOLD EXPRESSIVO (Startup, Consumer App, Gaming) -->
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Instrument+Sans:wght@300;400;500&display=swap" rel="stylesheet">

<!-- SOFISTICADO ORGÂNICO (Wellness, ESG, Cultura) -->
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,300&family=Outfit:wght@300;400;500&display=swap" rel="stylesheet">

<!-- HUMANISTA MODERNO (B2B, Saúde, Educação) -->
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Lora:ital,wght@0,400;1,400&display=swap" rel="stylesheet">

<!-- MINIMALISTA STARK (Portfólio, Agência, Arquitetura) -->
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@300;400;700;900&family=Figtree:wght@300;400;500&display=swap" rel="stylesheet">
```

---

### FASE 6 — Ícones (hierarquia obrigatória)

**Nunca use emojis como ícones funcionais.**

**React/JSX:**
```jsx
// Lucide React (preferido — stroke elegante, tree-shakeable)
import { ArrowRight, Zap, Shield, ChevronDown } from 'lucide-react'
// Uso: <ArrowRight size={20} strokeWidth={1.5} color="currentColor" />
```

**HTML Puro:**
```html
<!-- Phosphor Icons (mais expressivo, bom para consumer) -->
<script src="https://unpkg.com/@phosphor-icons/web@2.1.1"></script>
<i class="ph ph-rocket-launch" style="font-size:24px"></i>

<!-- Tabler Icons (excelente para dashboards) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont/dist/tabler-icons.min.css">
<i class="ti ti-dashboard"></i>
```

**Regras:**
- `strokeWidth={1.5}` para elegância; `strokeWidth={2}` para acessibilidade
- Ícones nav/UI: 18-20px; ícones de feature: 24-32px; hero icons: 48-64px
- Consistência: escolha UMA biblioteca e use em todo o projeto

---

### FASE 7 — Padrões de Layout 2025/2026

```css
/* BENTO GRID — estilo Apple/Linear */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 12px;
}
.bento-hero     { grid-column: span 8; grid-row: span 2; }
.bento-stat     { grid-column: span 4; }
.bento-feature  { grid-column: span 6; }
.bento-wide     { grid-column: span 12; }

/* TYPOGRAPHIC HERO — título como elemento visual */
.display-hero {
  font-size: clamp(3rem, 8vw, 7rem);
  line-height: 1.0;
  letter-spacing: -0.03em;
  font-weight: 700;
}

/* OVERLAP / DEPTH LAYER */
.layer-card {
  position: relative;
  transform: translateZ(0);
  transition: transform var(--duration-base) var(--ease-spring);
}
.layer-card:hover { transform: translateY(-4px) translateZ(0); }

/* GLASS CARD refinado */
.glass {
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.08);
}

/* NOISE TEXTURE */
.noise::before {
  content: '';
  position: absolute; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
  pointer-events: none; z-index: 0;
}
```

---

### FASE 8 — Animações com Propósito

```css
/* ENTRADA STAGGERADA */
@keyframes slide-up {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-in { animation: slide-up var(--duration-page) var(--ease-out) both; }
.stagger-1  { animation-delay: 80ms; }
.stagger-2  { animation-delay: 160ms; }
.stagger-3  { animation-delay: 240ms; }
.stagger-4  { animation-delay: 320ms; }

/* HOVER MAGNÉTICO */
.btn-hover {
  transition: transform var(--duration-base) var(--ease-spring),
              box-shadow var(--duration-base) var(--ease-out);
}
.btn-hover:hover {
  transform: translateY(-2px) scale(1.02);
}

/* SHIMMER LOADING */
@keyframes shimmer {
  from { background-position: -200% center; }
  to   { background-position: 200% center; }
}
.skeleton {
  background: linear-gradient(90deg, var(--color-bg-surface) 25%,
    rgba(255,255,255,0.05) 50%, var(--color-bg-surface) 75%);
  background-size: 200% auto;
  animation: shimmer 1.5s linear infinite;
}

/* GLOW INTERATIVO */
.glow-interactive {
  transition: box-shadow var(--duration-base) var(--ease-out);
}
.glow-interactive:hover {
  box-shadow: 0 0 0 1px var(--color-accent-default),
              0 0 20px rgba(var(--accent-rgb), 0.3);
}
```

---

### FASE 9 — Checklist Final (OBRIGATÓRIO antes de entregar)

**Design System:**
- [ ] Variáveis CSS definidas para TUDO: cores, tipografia, espaçamento, raios, motion
- [ ] 8pt grid aplicado (todos espaçamentos múltiplos de 8)
- [ ] Sistema de cores semântico (não apenas estético)
- [ ] Hierarquia visual clara em todos os screens

**Tipografia:**
- [ ] Fonte principal ≠ Inter/Roboto/Arial/sistema
- [ ] Escala tipográfica definida e aplicada consistentemente
- [ ] `letter-spacing` e `line-height` ajustados por tamanho
- [ ] Display/Hero tipo usa tamanho dramático (clamp ou 3rem+)

**Ícones:**
- [ ] Uma única biblioteca de ícones no projeto inteiro
- [ ] Tamanhos consistentes por contexto de uso
- [ ] Zero emojis em ícones funcionais

**Interatividade:**
- [ ] Hover states em TODOS os elementos clicáveis
- [ ] Focus states acessíveis (`:focus-visible`)
- [ ] Pelo menos uma animação de entrada com stagger
- [ ] Loading states / skeleton screens se houver dados assíncronos

**Responsivo:**
- [ ] Mobile-first ou pelo menos testado em 375px
- [ ] `clamp()` para tipografia fluida
- [ ] Grid/Flex sem overflow horizontal

**Qualidade:**
- [ ] Nenhum elemento "AI slop" (gradiente genérico, layout sem propósito)
- [ ] Contraste WCAG AA mínimo (4.5:1 para texto normal)
- [ ] Não parece template — tem personalidade e diferenciação visual

---

## Referências Rápidas

- `references/behance-queries.md` — Queries prontas por setor/tipo
- `references/palettes.md` — 10 paletas curadas prontas para usar
- `references/uiux-principles.md` — Guia completo de princípios UI/UX
- `references/typography-pairs.md` — Pares tipográficos por tom de projeto
- `references/designers-2025.md` — Designers e estúdios em destaque 2025/2026
