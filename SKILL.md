---
name: knight-imagetopptx-skill
description: Use when Codex must rebuild an existing slide image, screenshot, or image-only PPTX page into an editable .pptx replica, especially Chinese business report slides with editable text, cards, arrows, complex visuals, and independently movable generated image assets.
---

# Knight Image To PPTX

## Scope

Use this only for **existing visual slides**:

- A PNG/JPG/WebP slide image that must become editable PowerPoint.
- A PPTX whose slides are image-only screenshots or generated full-page images.
- A PDF or multi-page image set where each page must become an editable PowerPoint slide.
- A rendered slide page that needs editable text, containers, arrows, icons, and layout objects.

Do not use this for creating a new deck from scratch, SVG-only conversion, or simple image packaging where the user does not need object-level editing.

## Core Rule

Rebuild the slide semantically so the parts the user needs to edit are practical PowerPoint objects.

- Text, cards, panels, dividers, lines, simple arrows, bullets, badges, and tables: create as native PowerPoint objects.
- Icons, pictograms, complex badges, decorative marks, tiny UI glyphs, illustration-like elements, complex pictures, and complex visual objects: **must be generated with the image generation model as independent transparent PNG assets**, then inserted into the PPTX.
- Flowing ribbon arrows, migration streams, gradient arrow bands, multi-lane flow arrows, or any arrow system that needs soft fades, bundled curves, overlapping streams, or fused arrowheads is a complex visual object. Generate it separately with the image generation model and stitch it into the PPTX as one or a small number of transparent PNG visual assets; do not rebuild it from many native rectangles, triangles, or curve fragments.
- Source-image crops are reference material only. Do not use cropped screenshot fragments as final icon assets unless the user explicitly provides a real logo/brand mark that must remain exact.

## Mandatory Execution Contract

When this skill is triggered, the workflow below is binding, not optional guidance. Do not jump directly from screenshot to PPTX, and do not deliver a file unless the required evidence exists.

Before building, track the execution state in memory or local notes. Write `rebuild_execution_report.json` only once near the end as a compact final summary; do not repeatedly rewrite a verbose phase log. The final summary must cover these required phases:

- `input_prepared`: source path, slide/page count, slide size, aspect ratio, and output target recorded.
- `visual_inventory_done`: major text blocks, native objects, connectors, tables, cards, icons, and complex visuals listed with stable IDs.
- `asset_classification_done`: every non-text visual marked as `native_editable` or `imagegen_asset`.
- `imagegen_assets_done`: every `imagegen_asset` has an image-generation source, final transparent PNG, manifest entry, and contact sheet or crop QA.
- `text_fit_done`: every visible PPT text object was checked with `ppt_text_fit.py` or has a recorded exception; the report may be compact.
- `pptx_built`: editable PPTX generated with native text/shapes and independent image assets.
- `render_qa_done`: PPTX rendered to PNG and compared against the reference at full-page level.
- `local_crop_qa_done`: tight regions such as icon buttons, dense cards, tables, labels, bottom bars, and user-flagged areas cropped and inspected.
- `validation_done`: asset checker and relevant script/compile checks run, or blockers recorded.

If any phase cannot be completed, stop and report the blocker instead of silently skipping it. If the user asks for speed or a rough pass, still perform the minimum compact execution summary, asset manifest, rendered preview, and validation; mark the result as draft if QA is intentionally incomplete.

Final answers must include the PPTX path and the most important evidence paths, normally rendered preview, asset contact sheet, compact text-fit report, and notable crop QA. Do not claim completion from code generation alone.

## Non-Negotiable Image-Generation Gate

**Final icon and complex-visual assets must come from the image generation model.** Do not hand-draw, script-generate, trace, or approximate final icons with PIL, SVG, canvas, icon fonts, manually authored vector paths, or PowerPoint shape drawings. Those methods are allowed only for native editable primitives such as cards, lines, arrows, tables, separators, simple badges, and text containers.

Before rebuilding, classify every non-text visual region:

- `native_editable`: simple geometry that should remain editable in PowerPoint, such as panels, rounded rectangles, ordinary single arrows, table cells, divider lines, small numeric badges, and plain UI containers.
- `imagegen_asset`: icons, pictograms, logos that are not supplied as exact brand files, decorative skylines, illustration fragments, complex badges/seals, screenshots that should become stylized editable-adjacent assets, dense tiny glyph clusters, mascots/people/devices/scenes, complex pictures, flowing ribbon arrows, migration streams, multi-lane gradient arrows, or any visual whose faithful reconstruction would require custom drawing logic.

For every `imagegen_asset`, call the image generation model or reuse an asset that was already produced by that model for this rebuild. Keep the original generated file if the tool saves one, copy it into the working `assets/` folder, then cut/repack/clean it as needed into independent transparent PNGs. Record the generated source path or prompt in the asset manifest.

If the image generation tool is unavailable, blocked, or fails repeatedly, stop and report the blocker. Do not silently replace the required asset with a script-drawn or hand-authored substitute, and do not describe such a substitute as generated.

## Workflow

1. **Prepare input**
   - Create a working folder beside the source, e.g. `editable-replica-XX/`.
   - If the input is image-only PPTX or PDF, render/export each page/slide to PNG first and treat each rendered page as a reference image.
   - If the input is multiple images, preserve their order and treat each image as one target slide.
   - Record slide size, aspect ratio, source filenames/page numbers, and output path.
   - Start tracking the execution phases required by the Mandatory Execution Contract, but write the final `rebuild_execution_report.json` once after validation as a compact summary.
   - For multi-page inputs, each page is an independent single-slide rebuild task. Do not build page 2 by copying page 1 and making rough edits unless the visual page is genuinely repeated and the render check confirms it.

2. **Inventory the page**
   - Build a visual inventory: title/subtitle/body text, cards, panels, containers, arrows, connectors, icons, labels, footers, backgrounds.
   - Assign stable IDs to every non-text visual asset, e.g. `process_log_parse`, `output_excel_sheet`, `bottom_human_reviewer`.
   - Record approximate bounding boxes and target visual size for each asset.
   - Mark each non-text visual as either `native_editable` or `imagegen_asset` using the Non-Negotiable Image-Generation Gate above.

3. **Generate icons and visual assets**
   - Use the image generation model for every `imagegen_asset`. Prompt for isolated flat/vector-style assets with no text, no labels, no numbers, no card frame, no shadow unless visible in the reference.
   - **Color fidelity is a first-pass requirement.** Before prompting, sample/record every icon's reference colors: foreground stroke/fill, internal detail color, container/host color, and whether the icon is meant to be transparent, monochrome, white-on-color, color-on-white, or multi-color. The first image-generation prompt must state these color roles and approximate hex values per asset or per grid cell. Do not let the model choose a generic palette.
   - Treat color role as part of the asset identity. If the reference uses the same pictogram in different colors or states, generate separate color-specific assets or separate grid cells. If the generated asset's color role does not match the reference, mark it invalid and regenerate from the prompt/source sheet before PPT insertion; do not rely on PPT tinting, recoloring, opacity tricks, or later cleanup to repair a wrong first-pass color.
   - For complex visual regions, first analyze the semantic target and prompt the model for a clean rebuilt asset, not a pixel crop copy. Keep text outside the image whenever it can be native editable text in PowerPoint.
   - For flowing arrows, migration streams, ribbon bands, and other compound arrow visuals, generate the visual object as a transparent PNG asset. Prompt for the exact lane count, direction, color roles, fade behavior, curvature, arrowhead style, and empty center/edge zones needed for later PPT placement. If independent alignment is needed, split the generated source into a small number of semantic transparent assets, such as left-flow and right-flow; avoid fragmenting each lane or arrowhead into separate PPT objects.
   - Prefer a deterministic removable background for icon grids: request a solid pure chroma-key magenta background `#FF00FF`, no checkerboard, no texture, no shadow, no gradient, and no transparency in the source sheet. Then chroma-key it into true transparent RGBA assets. Use direct transparent generation only when the output tool reliably returns real alpha.
   - Asset grids are allowed only with explicit `C×R` / `N×M` alignment rules, where `C` or `N` is column count and `R` or `M` is row count. This covers square `N×N` grids and rectangular grids such as `5×4` or `4×2`.
   - In the image-generation prompt, state the grid dimensions exactly: `C columns × R rows`, overall canvas ratio `C:R`, equal-size cells, visible or intentionally empty gutters between cells, each icon centered on its own cell center, each icon constrained to the central 55-65% safe zone, and at least 20-25% empty chroma-key padding inside every cell. Require no clipped edges, no overflow into gutters, and no cross-cell overlap.
   - For square `N×N` grids, request a square canvas and `N` equal rows/columns. For rectangular `C×R` / `N×M` grids, request a canvas whose aspect ratio matches the column:row ratio. Edge cells must use the same safe-zone and padding rules as interior cells. Do not hard-code `5×4`, `4×2`, or any specific grid size; pass columns and rows as parameters.
   - When converting a generated chroma-key grid to transparent PNGs, use per-cell edge-sampled adaptive chroma-key thresholds. For each `C×R` / `N×M` cell, sample that cell's outer edge pixels as the local background, compute the magenta color-distance cutoff from high-percentile edge distances plus a safety margin, and key only that cell with its own cutoff. Do not rely on one global fixed threshold for the whole sheet; generated magenta backgrounds can vary slightly and create semi-transparent colored halos.
   - Each cell must be cut into exactly one semantic asset. Avoid mixing multiple icons into one asset.
   - Do not trust grid math alone. After cutting an asset grid, remove cross-cell fragments and inspect a contact sheet of the final independent PNGs. If any icon contains stray arcs, dots, wedges, clipped strokes, partial marks from adjacent cells, or edge-cell clipping from the generated sheet itself, treat the grid as invalid and regenerate the grid with stricter safe-zone, gutter, and padding constraints before inserting assets into PPT.
   - After cutting, normalize each PNG to a square transparent canvas with generous safety padding. Target: at least 10 px transparent edge padding. Center by alpha visual centroid, not only by the alpha bounding box center; asymmetric icons such as targets, stars, rays, arrows, and magnifiers can look off-center when bbox-centered.
   - Store generated source sheets under an `assets/source/` or equivalent source folder and keep the final asset directory limited to independent transparent PNGs that will be inserted into PPT. This prevents source sheets from being mistaken for final assets during QA.
   - When inserting into PPT, scale by the asset's non-transparent alpha extent and align by alpha centroid, not by the full transparent canvas. Preserve aspect ratio; do not stretch icons to fill arbitrary target boxes.

4. **Rebuild the PPTX**
   - Use `python-pptx`, PowerPoint automation, or the repo's established PPT tooling.
   - Prefer native slide background fill for plain white/off-white pages (`slide.background.fill`) instead of adding a full-slide white rectangle shape. Only use a bottom background rectangle when it carries visible editable decoration that PowerPoint background fill cannot represent.
   - Use native PowerPoint text boxes for all readable text. Do not rasterize editable text into images.
   - Use native shapes for rounded cards, panels, borders, separator lines, dashed lines, and ordinary arrows.
   - For rectangle-like objects such as section headers, title bars, pills, metric cards, tabs, and label strips, use native `RECTANGLE` or `ROUNDED_RECTANGLE` shapes. Do not use ribbon, chevron, triangle, or freeform tail helpers unless the source visibly has a real slanted notch or flag tail.
   - Insert generated complex visual assets such as flowing ribbon arrows, dense screenshots, and illustration-like regions as transparent PNGs positioned behind or between native objects according to the reference. Scale by visible alpha bounds and align to measured target edges; keep editable labels, cards, center circles, legends, and callouts as native PPT objects above or around the asset.
   - For direction-sensitive native shapes such as funnels, trapezoids, chevrons, arrow wedges, triangular tabs, and slanted badges, do not rely on the default PowerPoint orientation. Compare the rendered direction against the reference and rotate or rebuild with a native freeform path when needed.
   - Control PowerPoint rounded rectangles explicitly. `MSO_SHAPE.ROUNDED_RECTANGLE` defaults to huge capsule corners on some aspect ratios; set `shape.adjustments[0]` around `0.025-0.08` and verify in render.
   - Use one generated PNG per icon/complex visual, with transparent background and no clipped edges.
   - Do not stretch icons. Preserve aspect ratio and center by alpha content box.
   - Before writing dense table cells, cards, button labels, mixed Chinese/English labels, and any long title/subtitle, run a text-fit preflight instead of guessing font sizes. Actually call `scripts/ppt_text_fit.py` with the target exported pixel bbox, intended font, bold state, and reference max line count; use its `recommended_pt` as the first build size and save a compact `text_fit_report.json` or equivalent evidence file.
   - Text-fit coverage is based on the final visible text, not on whether a helper named `add_fitted_text()` was used. Every code path that creates PowerPoint text must have fit evidence before writing the text: `add_text()`, manual `text_frame` edits, `paragraph.add_run()`, mixed-style number/unit lines, table cells, badges, labels, legends, chart/axis labels, and small UI captions. Hard-coded run sizes are allowed only after fitting the complete visible phrase or each declared sub-box, and the report must name the text object that was fitted.
   - Avoid both extremes: do not let text overflow, cross table borders, or force unintended line breaks; also do not shrink text below the visual hierarchy of the reference just to make it fit. If text only fits after becoming visibly too small for its role, first widen the text box, reduce margins, adjust column widths, or allow the same wrap pattern as the reference.
   - For Chinese text in `python-pptx`, set the East Asian typeface in OOXML (`a:ea`) as well as `run.font.name`; otherwise PowerPoint may fall back to Songti/serif fonts and shift the layout.
   - Treat repeated label/button components as responsive, not fixed. Mixed English+Chinese labels such as `Agents 工作流` often need a smaller font, wider text box, or adjusted text offset compared with pure Chinese labels.
   - Build tool/example buttons as native button shapes plus one independent icon PNG plus editable text. Do not bake labels such as `Doc`, `PPT`, `frontend`, `imagegen`, or `GitHub` into the icon image.
   - For circular process loops, avoid relying only on curved connectors when the reference uses smooth arc arrows. Use true PowerPoint native arc/arrow objects or high-precision open freeform curve paths. Do not simulate smooth arcs with many separate straight connector segments; visible joints and selection-pane clutter are real defects.
   - When an arc loop needs several curved arrows, make each arc segment one continuous editable object and group the segments into one top-level visual object. Name the group descriptively, e.g. `center_cycle_curved_arrows_group`, so the user can move the loop as one object while still being able to ungroup for edits.
   - Run a final layer-order pass before rendering. Hard rule: **preserve native internal order; only lift icons and text**. Keep native objects' internal visual order, bring image-generation icon assets above native objects, then bring all text to the top. Shapes must not cover editable text, and icons should not cover labels.
   - Prefer building each component in natural visible order: native container/card first, then its icon/image asset, then its editable text. Do not do a blind whole-slide XML reorder when component-local order already gives the correct visual stack.
   - After any z-order change, verify the rendered PPT crop, not only the PPTX shape list. A picture can exist in the PPTX and still be hidden behind later native shapes if the physical PowerPoint shape-tree order is wrong.
   - Keep faint construction rings and guide circles subtle. Translucent PPT oval strokes stack and can become unwanted gray rings after export; delete ambiguous rings or use very high transparency and clear inherited shadows.

5. **Render and compare**
   - Render the rebuilt PPTX to PNG using PowerPoint export when available.
   - Produce a visual preview/contact sheet and compare against the reference.
   - Iterate on obvious mismatches: icon clipping, icon size, arrow direction, text wrapping, card borders, alignment, and spacing.
   - Crop crowded regions for QA, not only the full slide. Save 1:1 PNG crops for bottom tags, dense cards, circular diagrams, right-side tool panels, feedback bars, and any selected-object complaints.
   - For every tight icon slot, especially button/tool/UI icons, render a 1:1 local crop of the inserted PPT region. Asset thumbnails are not enough: verify the final rendered PPT does not show clipped edges, stray fragments, or adjacent-cell debris.
   - For multi-page inputs, render and compare every rebuilt slide against its own source page. Fix mismatches page-by-page before final delivery.

6. **Assemble multi-page output**
   - For multiple source images/pages, append all independently rebuilt slides into one `.pptx` in the original order.
   - Keep per-page assets, manifests, rendered previews, and QA crops traceable by slide/page number.
   - Do not deliver separate PPTX files unless the user explicitly asks; the default deliverable is one combined editable PPTX.

## Implementation Patterns

- **CJK font XML:** after setting `run.font.name`, also set `a:latin`, `a:ea`, and `a:cs` `typeface` on the run XML. Use this for every Chinese text run.
- **Text-fit preflight:** for every dense table cell, card title/body, subtitle, button label, and icon-adjacent label, estimate text width/height before generating the PPTX. Prefer the bundled helper:

```bash
python scripts/ppt_text_fit.py --text="升级方向不是少做事，而是更会定义、拆解、验收和复盘。" \
  --box 980x42 --font "Microsoft YaHei" --max-pt 22 --min-pt 12 --max-lines 1
```

Use the returned `recommended_pt` and `lines` to set the first PPT build, but keep the final `text_fit_report.json` compact. It should record only: `called`, `notfits`, `exceptions`, and `key_long_texts` that are most likely to regress. Do not write every successful short-label fit by default; keep full per-shape details only in temporary debug data when actively diagnosing a failure. The helper uses Windows font files, slide export scale, visible glyph bounding boxes, CJK-aware wrapping, binary search, safety margins, robust argparse handling for leading-minus text, and forced UTF-8 stdout for Chinese/symbol JSON output. If the helper is unavailable, use PIL `ImageFont.truetype()` with Microsoft YaHei/SimHei/Arial and the same logic; only fall back to rough CJK estimates as a last resort. Do not use raw font ascent+descent as the only line-height estimate; it over-counts invisible YaHei padding and makes labels too small.
- **Text argument safety:** when calling `ppt_text_fit.py` from Python or shell, pass text as `--text=<value>` instead of `--text <value>`. This prevents values that begin with minus signs, plus signs, dash variants, arrows, parentheses, or symbol-heavy metric prefixes from being misread as command options. If a wrapper constructs subprocess arguments, build `f"--text={text}"` as one argv item.
- **Strict text-fit coverage:** do not restrict fitting to a single wrapper such as `add_fitted_text()`. Treat every text-producing operation as in scope, including `add_run()` branches, direct `shape.text_frame` edits, table cell text, manually composed numeric metrics, badge labels, split title/body runs, chart labels, and footer notes. For mixed-size metric lines such as number+unit, English acronym+number+unit, signed value+unit, or value+trend-symbol combinations, fit the full visible phrase against the whole bbox first, then derive number/unit run sizes from that fitted base size or fit the number and unit in explicit sub-boxes. Track coverage internally while building. The final compact `text_fit_report.json` should include `called`, `notfits`, `exceptions`, and representative `key_long_texts`; only failed, exceptional, or high-risk long text needs per-object detail.
- **Manual run exception discipline:** if a tiny decorative label, page number, or intentionally fixed-size badge truly cannot use `ppt_text_fit.py`, record it under `exceptions` in the compact report with its bbox and reason, then verify it with a local render crop. Unreported hard-coded text sizes are a defect.
- **Reference line-count lock:** derive the target max line count from the source image before fitting. One-line source labels must be fitted as one line; two-line source titles must remain two lines. Do not insert manual line breaks that create more lines than the reference unless the source visibly does so.
- **PPT point-to-pixel scale:** calculate from the actual export setup, not from memory. For 1672 px wide output on a 13.333333 in slide, `px_per_pt = (1672 / 13.333333) / 72 ~= 1.742`; the helper applies this scale plus a render fudge. If using a different slide size or export width, pass `--slide-px` and `--slide-in`.
- **Role text hierarchy:** keep font sizes flexible and derived from the reference page, not fixed numeric ranges. Preserve the relative hierarchy between title, subtitle, card titles, table headers, table body, tool names, labels, and notes. If text only fits by becoming visibly weaker than peer text in the same role, adjust geometry, margins, columns, or wrapping instead of silently accepting tiny text.
- **Overflow guards:** table body text should stay inside its own cell with at least 10-16 px visual padding from vertical grid lines. Card text should reserve icon space first, then fit only in the remaining text area. For one-line reference labels, do not allow accidental wrapping; for multi-line reference labels, match the observed line count and line spacing. Treat mixed CJK/Latin labels such as `看 diff、看运行结果` as wider than CJK-only text and give them extra width or a smaller role-consistent size before rendering.
- **Card text centering:** for pills, buttons, workflow cards, and icon+label cards, align the text box to the full intended visual slot and set vertical anchoring to middle (`MSO_ANCHOR.MIDDLE` or equivalent). Do not place a smaller text box by eyeballing baseline position. Card body text should be vertically centered within its reserved area when the reference is centered, with line count and line spacing matching the reference.
- **Reserved trend/arrow slots:** for compact metric rows that combine a label, signed value, unit, and trend arrow/icon, divide the row into explicit label, value, and arrow/icon slots before fitting text. The fitted text bbox must exclude the arrow slot; the arrow should be anchored inside its own reserved slot with enough padding from the card edge. Do not place trend arrows by absolute x-offsets that can overlap longer percentages or mixed number/unit runs. Render a local crop for these dense rows before delivery.
- **Trend arrow shape fidelity:** if the reference shows a thick trend arrow with a filled shaft and triangular head, build it as a native PowerPoint arrow shape such as `UP_ARROW` or `DOWN_ARROW`, not as a text glyph, thin connector, or line with arrowhead. Reserve a separate arrow slot and keep the metric text editable beside it.
- **Responsive card layout:** repeated cards may need per-card geometry overrides. Do not force one divider position, text offset, or body width formula across all cards when titles or mixed Chinese/English body text differ. Adjust divider x-position, body box width, icon slot, and title/body font scale per card, then verify with local crops.
- **Undersize guards:** if fitted text uses little of the available width and looks visibly smaller than neighboring peer labels, raise it toward the peer/reference scale. Avoid overcorrecting from overflow into a weak, under-scaled table.
- **Chroma-key icon sheets:** for icon sheets, prefer a solid pure magenta `#FF00FF` source background over checkerboard or near-white backgrounds. Chroma-key by color distance, preserve intentional white internal details only for assets that need them, then output true RGBA PNGs. For generated `C×R` / `N×M` sheets, compute the keying threshold per cell from that cell's edge pixels instead of using one global fixed threshold; use a high edge-distance percentile plus margin as the local background cutoff, fade to full alpha over a narrow distance band, and zero out low residual alpha. Keep the magenta source sheet in `assets/source/`; do not leave source sheets in the final asset directory used by `check_rebuild_assets.py`.
- **Generic `N×M` cutting:** implement grid cutting with explicit `columns` and `rows` parameters. Validate that the asset spec count equals `columns * rows`, compute cell bounds from these parameters, and never hard-code a specific grid such as `5×4` or `4×2`. Save grid dimensions, source path, per-cell bbox, and centering metrics to the asset manifest.
- **Centroid-centered repacking:** after chroma-key cutting, crop to the alpha bbox, then repack each asset into a square transparent canvas using the alpha visual centroid as the center. Record post-pack centroid delta and keep it near zero. Bounding-box centering alone is insufficient for asymmetric icons such as target arrows, people/star groups, heads with rays, magnifiers, and wide trend marks.
- **Alpha image placement:** inspect each transparent PNG's alpha bbox and alpha centroid. Scale by visible alpha extent and align the centroid to the target slot center, then place the full transparent canvas accordingly. This keeps transparent safety padding without shrinking or visually offsetting icons.
- **Complex visual object placement:** when a flow ribbon, migration stream, complex illustration, dense UI screenshot, or other complex picture is classified as `imagegen_asset`, treat it as a designed visual layer. Generate it without editable text where possible, clean it into true RGBA, then place it by measured visible-alpha edges. Keep native editable objects such as center circles, cards, tags, legends, callouts, and labels above it. Split the generated source only by semantic region needed for alignment, e.g. left stream and right stream, not by every small lane or arrowhead.
- **Icon color contract:** first-pass image-generation prompts must include exact visual color roles from the reference. For each asset, record sampled/estimated hex colors and specify foreground stroke/fill, internal details, background or host shape color, and whether the color belongs to the icon itself or its container. If a grid mixes colors, specify each cell's colors explicitly. The asset manifest should include the intended color role or sampled hex notes for every icon. A color-mismatched icon is an invalid asset and should be regenerated or replaced by a correctly colored image-generation-derived variant before PPT insertion.
- **Content-grid cutting:** for generated asset sheets, first detect the real `C×R` / `N×M` content grid before cutting. Build a foreground mask from chroma-key distance or another reliable alpha/color mask, project foreground pixels on X and Y, detect exactly `C` column centers and `R` row centers, then compute cell edges from adjacent center midpoints. Cut cells from these detected edges, not from `(0,0)` equal image division, unless the prompt deliberately produced a full-sheet uniform grid with no outer margin ambiguity and detection confirms it. If the detected center count does not match the declared columns/rows, reject the sheet and regenerate. Save detected centers, edges, per-cell bbox, and padding failures to the asset manifest or grid alignment report.
- **Rounded rectangles:** after creating `ROUNDED_RECTANGLE`, set `shape.adjustments[0]`; use smaller values for large panels (`0.025-0.04`) and slightly larger values for pills/buttons (`0.06-0.10`).
- **Rectangle-like header discipline:** section headers and title bars that read as rectangular should be native rectangles or rounded rectangles only. Avoid adding triangle tails, ribbon slants, chevrons, or freeform wedges as decorative construction unless the reference clearly shows them. If a helper named `ribbon` or similar creates extra points, replace it with a plain native rectangle and verify the local crop.
- **Effect hygiene:** PowerPoint shapes, pictures, charts, and connectors can inherit theme effects even when the reference is flat. After creating every shape class, explicitly clear shadow, glow, soft-edge, reflection, and effect-list XML unless the source visibly requires that effect. Run a final slide-level effect cleanup before saving, then verify the PPTX XML has no unexpected `outerShdw`, `glow`, `softEdge`, or `reflection` nodes.
- **Line restraint:** do not add divider lines, connector strokes, or panel borders just because they help construction. Every line must correspond to a visible reference line or a needed native boundary. Match line weight and opacity conservatively; if a line reads as darker than the screenshot, reduce width/color instead of accepting a visual grid that was not in the source.
- **Tool buttons:** compose each button from a native rounded rectangle, `add_picture(icon_id, ...)`, and `add_text(label, ...)`. Tune icon slot, text offset, and font size per label.
- **Wide icon slots:** magnifier, loop, sync, person-loop, and arrow-heavy icons often have a much wider transparent canvas or handle than square symbols. In tight cards, give these icons smaller/lower-left slots or a dedicated variant so both the visible icon and the PPT selection box stay clear of text.
- **Smooth arc arrows:** when using open freeform curves, build each visible arc as one path with native line styling and native arrowhead, not many separate line shapes. Use a high internal coordinate scale before converting to PPT coordinates so PowerPoint's integer path coordinates do not create jagged or stepped arcs. Prefer rounded line caps/joins when available, and group related arc paths after creation.
- **Pie/doughnut and center-circle discipline:** for pie/doughnut charts, radial dashboards, and large circular KPI nodes, first list the visible roles: outer ring, main fill circle, hollow center, center label, icon, and any real highlight. Derive every overlay from the same measured center. If the source only shows an outer stroke, create it as no-fill stroke; do not fill it with white. Do not add decorative highlight ovals, glow circles, white backing circles, or extra center disks unless they are visibly present in the reference. Include a tight center crop proving there is no stray or off-center circle.
- **Layer-order pass:** after building and grouping, classify shapes into text, image assets, and native objects. Generate with the principle **"preserve native internal order, only lift icons and text"**. Preserve the existing internal order of native objects unless a specific mismatch requires a local fix; do not blindly send every native object to the back, because this can hide colored pills, center fills, or foreground lines behind white panels/rings. Bring image assets/icons forward, then bring all text boxes/text shapes to the very front. Preserve intentionally grouped native visuals as one object, but keep them in the native-object layer unless they are icons.
- **Icon render-layer safety:** do not trust `slide.shapes` enumeration or object existence as proof that inserted PNG icons will render above cards. PowerPoint renders by the physical shape-tree order in `ppt/slides/slideN.xml`; a mistaken `_spTree.append()`, `insert_element_before()`, or mutation-while-iterating helper can place `pic` nodes before later `sp` nodes, making icons disappear behind white cards while the PPTX still contains the pictures. Prefer component-local creation order over global XML surgery. If a global lift is necessary, collect stable shape references first, move them with one vetted helper, then inspect the saved slide XML order and render a crop proving each icon is visible in its final slot.
- **Missing-icon diagnosis:** when icons do not appear in the rendered PPT, check z-order before regenerating assets. Confirm: the PNG has non-empty alpha, the picture dimensions are non-zero, the `pic` node is after its card/container shape and before/top of text as intended, and a local rendered crop shows the icon. If asset contact sheet is correct but render is blank, it is usually a layer-order problem, not a chroma-key problem.
- **Local crop QA:** after rendering, crop suspicious regions with PIL and inspect them separately. Do this before final delivery when a slide has tight labels, right-side tool grids, or bottom feedback bars.
- **Asset manifest proof:** include for every `imagegen_asset` its prompt summary, generated source path when available, final PNG path, and any cleanup/cutting operation. If an asset has no image-generation source, it is not a valid final icon/complex asset.

7. **Validate before delivery**
   - Run the bundled helper:

```bash
python scripts/check_rebuild_assets.py --asset-dir path/to/assets
```

   - Open or inspect the rendered PNG before claiming completion.
   - Write the compact final `rebuild_execution_report.json` once, and confirm it has no incomplete required phase unless the final answer explicitly labels the output as a draft and explains the missing evidence.

## Lessons From Real Repairs

- Prevent icon clipping by requiring the generated grid itself to keep every icon fully inside its own cell, then cut by verified grid cells and repack content into a larger transparent canvas.
- For generated icon sheets, solid magenta `#FF00FF` chroma-key backgrounds are more reliable than checkerboard backgrounds. Checkerboard pixels can leak into colored strokes; magenta can be removed by color distance while preserving white internal icon details.
- Generated magenta is not always perfectly uniform. Per-cell edge-sampled adaptive chroma-keying prevents pale background blocks and semi-transparent halos, and it generalizes cleanly from square `N×N` sheets to rectangular `C×R` / `N×M` sheets.
- After cutting icons, center by alpha visual centroid, not just by the alpha bbox. Explorer thumbnails often expose this issue before PPT: asymmetric icons can pass padding checks while still looking visually off-center.
- Grid cutting must stay generic. Use parameterized `columns × rows` / `N×M` logic and fail if the provided asset spec count does not match the grid; do not copy a previous slide's `4×2` or `5×4` constants into a new task.
- Generated sheets often contain outer margins even when the prompt asks for a strict grid. Detect the real content centers first, then cut from center-midpoint edges; naive equal slicing from the image origin can erase whole icons or clip edge cells while still producing a plausible contact sheet.
- Color fidelity must be specified during the first image-generation attempt. Assets with different foreground colors, container colors, internal detail colors, or state colors should be treated as distinct targets; do not rely on a generic icon palette when the reference assigns specific colors to specific assets or states. A contact sheet that looks structurally correct but uses the wrong color role is still a failed asset sheet.
- The word "generated" is not enough. A script-drawn PNG is still a hand-authored substitute and violates this skill for icons and complex visuals. Use the image generation model first, then post-process the generated image.
- Asset sheets can leak adjacent-cell fragments into button icons. Treat stray bottom arcs, dots, wedges, or partial marks as a real grid/cutting failure even if the cut asset passes padding checks. Fix the grid prompt, alpha-component cleanup, or recutting logic, then re-render the actual PPT crop.
- Edge cells in a generated icon sheet must have the same safe-zone and padding as interior cells. Do not accept a grid sheet with edge-cell clipping, overflow, or cross-cell overlap.
- Windows Explorer thumbnails may expose edge problems sooner than PPT. Treat any thumbnail clipping as a real asset bug.
- If keying a non-transparent background, do not remove colors that are part of the icon palette. Green-screen cleanup can destroy green icons; checkerboard cleanup can leave gray edges.
- Ordinary single arrows, straight connectors, and simple chevrons can stay native. Flowing ribbon arrows, migration streams, gradient arrow bands, multi-lane arrow systems, and fused arrowhead streams should be generated with the image generation model as transparent complex visual assets, then layered into the PPTX with native text and surrounding objects preserved above them.
- Direction-sensitive shapes can be visually reversed by PowerPoint defaults. Funnel stages should be checked against the reference for top/bottom width and slant direction; if the built-in shape points the wrong way, rotate it or rebuild it as an editable native freeform instead of accepting the default.
- Text fitting must be handled before first render, not only by approximate coordinates. Use a preflight fit guided by the reference hierarchy, then check the rendered PPT and local crops. Widen boxes, adjust columns, or reduce font size only when it still preserves the same visual role as neighboring text.
- PowerPoint text is usually wider/taller than a naive pixel guess. First-build failures often come from guessing font sizes from screenshot pixels. Use `scripts/ppt_text_fit.py` with the real exported pixel bbox, font, bold state, and reference line count before writing the PPTX.
- Calling `ppt_text_fit.py` means actually executing it and preserving compact evidence, not merely applying its rule by memory. A slim `text_fit_report.json` with `called`, `notfits`, `exceptions`, and key long-text samples is enough for routine runs; expand to per-object debug only when fixing a concrete overflow.
- Leading-minus, leading-plus, dash-leading, arrow-leading, parenthesis-leading, and other symbol-leading metric text is a known argparse trap. Always include representative signed values, trend-arrow phrases, parenthesized labels, and mixed number/unit strings during verification; the report must not contain JSON parse exceptions from helper stderr or empty stdout.
- `ppt_text_fit.py` must emit UTF-8 JSON on Windows. Chinese text, symbols, and ranking glyphs should not require every caller to set `PYTHONIOENCODING`; the helper owns its stdout encoding.
- Text-fit evidence must cover manual runs too. Mixed numeric metrics and split-run labels are common overflow sources because they bypass `add_fitted_text()`; fit the whole visible phrase or declared sub-boxes before adding runs, and fail the QA pass if the final PPT contains untracked text-producing code paths.
- CJK font assignment must survive PowerPoint export. If the render shows serif/Songti-like glyphs, set `a:latin`, `a:ea`, and `a:cs` typefaces in the run XML.
- Reused tag/button components need per-label overrides. If a label mixes English and Chinese, test a local crop and tune `font_size`, `text_offset`, or width before final delivery.
- PowerPoint rounded rectangles can turn into oversized capsules. Always adjust corner radius and render-check large panels, cards, and small tool buttons.
- Rectangular section headers are not ribbons by default. If a title strip only looks like a blue rectangle, build it as a native rectangle/rounded rectangle; extra triangular tails are visible defects.
- Right-side tool panels should stay editable: native rounded buttons, generated icon PNGs, and separate text labels.
- Avoid leaving a full-slide white rectangle at the bottom of the selection pane. It usually comes from using a shape as the page background; use native slide background fill for plain backgrounds so the editable object list stays clean.
- Faint decorative rings are easy to overbuild. If the user sees extra gray circles, reduce the number of ellipses, increase transparency, and clear shadows; keep only rings visible in the reference.
- For circular workflows, freeform arc arrows can match the reference better than connector curves while staying editable. Each visible arc should be a continuous native arc/freeform path with its own arrowhead; a grouped set of paths is acceptable, but a stack of short straight segments is not.
- For rounded dashed feedback loops, first try a single editable open freeform path with PPT native dashed line styling and a native tail arrow. This gives the cleanest selection pane and preserves editability. PowerPoint's built-in connector types are only straight/elbow/curve, so use a freeform path when the loop needs multiple bends. If that renders poorly, fall back to whole native dashed connectors for straight runs and segmented elbows only.
- Card and pill labels should be centered by geometry, not by visual luck. Use the full pill/card text slot with middle vertical anchoring, then render a crop; if the text appears high/low or clipped, fix the text box and anchoring before changing font size.
- Text overflow must be treated as a layout bug, even if it is only a few pixels beyond a card border. For repeated cards, tune each card's divider, body width, and mixed-language text size independently rather than shrinking every peer card.
- Dense metric cards with trend arrows are overlap-prone. Reserve an arrow slot first, fit the label/value only in the remaining text box, and check a crop whenever the reference has long percentages, signs, units, or up/down arrows in the same row.
- Filled trend arrows are shapes, not text. Text arrows often render too thin and font-dependent; use native filled arrow shapes when the source arrow is visibly thick.
- Doughnut, radial, and KPI center overlays should be computed from the chart/plot center or circle bbox, not nudged by eye. After changing chart size, hole size, callout labels, or center-node size, re-center the overlay circle and text from the same coordinate source and verify with a tight crop. A common defect is an unintended extra white/highlight disk from a reused helper such as `outer_ring`, `center_white`, or `highlight`; remove any center circle whose role is not explicitly visible in the reference.
- Theme effects are a hidden source of false fidelity. If the source is mostly flat, clear default shadows and effects globally; a subtle PowerPoint shadow can make cards, arrows, and headers look like extra objects.
- Extra construction lines are defects, not harmless decoration. Keep separators and helper borders only when the reference visibly contains them, and tune weight/color from a rendered crop.
- Z-order is part of fidelity. If text or icons seem clipped, dim, hidden, or missing from the PowerPoint render, inspect the physical slide layer order before changing content. The default final stack should be text, then icons/images, then native containers/arrows/lines, while preserving the native layer's own internal foreground/background order. A clean asset contact sheet is not enough; icon visibility must be proven by the rendered PPT crop.
- When an output PPTX is open and locked, write a new versioned filename instead of killing the user's app or overwriting their open file.

## Deliverables

Return the final `.pptx` path plus, when produced:

- Rendered PNG preview.
- `assets/` folder of generated transparent icon PNGs.
- Asset manifest or visual inventory.

Mention any remaining limitation plainly, especially if a complex icon is a generated approximation rather than a perfect vector recreation.
