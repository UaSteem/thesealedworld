# Shared game viewport contract

Owner decision: 2026-10-25. Task: `tasks/active/2026-10-25-game-shell-contract.md`.
This target applies to prototypes and future gameplay interface redesigns. It
supersedes experimental Lab sizing. It does NOT mean runtime or Lab migration
has already been completed or accepted.

## Persistent shell

```text
page-wide header: approximately 40 CSS px
         central container: max 1920 CSS px, horizontally centered
         +------------------+--------------------------------+
         |                  | Phaser central gameplay area   |
         | HTML character   |                                |
         | status           +--------------------------------+
         |                  | HTML chat                      |
         +------------------+--------------------------------+
optional page-wide footer: up to approximately 40 CSS px
```

- The 1920px cap applies to the COMPLETE central container: status + field + chat.
  It does not cap the canvas alone or constrain the page-wide header/footer.
- At browser content width 2560px, a 1920px central container has 320px external
  margins on each side. These margins are not empty space inside the canvas.
- Central height uses the available browser CONTENT viewport minus the actual
  header, optional footer and explicitly approved spacing. Do not use monitor
  dimensions including browser chrome.
- The owner's subsequent explicit temporary value is a TOTAL 100px vertical
  reserve: physical central height = browser content height - 100px. Do not cap
  this result at 1080 or shrink it again because the central width is capped.
  This reserve alone does not authorize adding a footer or choosing its content.
- Do not impose a fixed 1080px height or vertically center a 1920x1080 mockup.
  Width limits do not authorize a corresponding fixed-height limit.
- Header target is approximately 40px. The optional footer is small (up to about
  40px) and holds version/minor information; do not add it solely for this plan.
- The left HTML status column persists. The right column contains Phaser above
  HTML chat. Changing chat height resizes the Phaser frame, not this arrangement.
- Reuse theme tokens and shared shell ownership across game screens.

## Four required desktop checkpoints

| Browser content size | Central width | Component sizing profile |
| --- | --- | --- |
| 2560x1440 | max 1920, centered | same base sizes as Full HD |
| 1920x1080 | available width, max 1920 | base |
| 1600x900 | available width | medium |
| 1366x768 | available width | compact |

The intended result is two controlled sizing transitions below the base profile,
not four unrelated layouts. Status, field and chat must remain coherent. Extra
height at 2560 may increase available space; it does not automatically enlarge
all fonts, controls or status components. Check reduced browser content height
separately instead of shrinking the whole page to fit an artificial rectangle.

Exact status widths, chat heights, spacing, minimum readable font/control sizes
and intermediate breakpoint thresholds are NOT approved numbers yet. Measure and
propose them explicitly. Do not silently invent them or freeze current prototype
values as the contract. Do not independently shrink only the field while leaving
status and chat at unrelated scales. Mobile/tablet work is deferred.

## Boundaries for all later interface work

- After shell implementation and owner acceptance, ordinary gameplay interface
  work changes only Phaser viewport CONTENT. Preserve header/footer, the central
  cap, status/chat arrangement and the approved sizing profiles.
- Combat, travel/rifts, inventory and dialogue are central-area content. An HTML
  overlay may be used without introducing another page shell.
- Top-down and perspective are separate display arrangements of shared state.
  A requested change for one must not silently change the other.
- A shell change requires a separately agreed task: identify the exact changed
  shell property and affected checkpoints before implementation.
- The prototype must reproduce future game framing. Laboratory/debug headings,
  preview boxes and extra margins must not consume game space or alter geometry.

## Verification and status

For shell work, record all four actual browser content sizes, header/footer
heights, central/status/chat bounds and Phaser host/backing/display dimensions.
Check pointer mapping, scrolling, overlays and chat resizing. Screenshots follow
the owner's current request. Geometry passing is not visual acceptance.

For scene-only work, verify shell measurements remain unchanged. Separate local
checks, runtime integration and owner acceptance. Current owner review policy:
prototype self-checks; independent review for existing game-code changes or
integration into the game codebase.
