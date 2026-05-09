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
- Icons, pictograms, complex badges, decorative marks, tiny UI glyphs, and illustration-like elements: **must be generated with the image generation model as independent transparent PNG assets**, then inserted into the PPTX.
- Source-image crops are reference material only. Do not use cropped screenshot fragments as final icon assets unless the user explicitly provides a real logo/brand mark that must remain exact.

## Non-Negotiable Image-Generation Gate

**Final icon and complex-visual assets must come from the image generation model.** Do not hand-draw, script-generate, trace, or approximate final icons with PIL, SVG, canvas, icon fonts, manually authored vector paths, or PowerPoint shape drawings. Those methods are allowed only for native editable primitives such as cards, lines, arrows, tables, separators, simple badges, and text containers.

Before rebuilding, classify every non-text visual region:

- `native_editable`: simple geometry that should remain editable in PowerPoint, such as panels, rounded rectangles, arrows, table cells, divider lines, small numeric badges, and plain UI containers.
- `imagegen_asset`: icons, pictograms, logos that are not supplied as exact brand files, decorative skylines, illustration fragments, complex badges/seals, screenshots that should become stylized editable-adjacent assets, dense tiny glyph clusters, mascots/people/devices/scenes, or any visual whose faithful reconstruction would require custom drawing logic.

For every `imagegen_asset`, call the image generation model or reuse an asset that was already produced by that model for this rebuild. Keep the original generated file if the tool saves one, copy it into the working `assets/` folder, then cut/repack/clean it as needed into independent transparent PNGs. Record the generated source path or prompt in the asset manifest.

If the image generation tool is unavailable, blocked, or fails repeatedly, stop and report the blocker. Do not silently replace the required asset with a script-drawn or hand-authored substitute, and do not describe such a substitute as generated.

## Workflow

1. **Prepare input**
   - Create a working folder beside the source, e.g. `editable-replica-XX/`.
   - If the input is image-only PPTX or PDF, render/export each page/slide to PNG first and treat each rendered page as a reference image.
   - If the input is multiple images, preserve their order and treat each image as one target slide.
   - Record slide size, aspect ratio, source filenames/page numbers, and output path.
   - For multi-page inputs, each page is an independent single-slide rebuild task. Do not build page 2 by copying page 1 and making rough edits unless the visual page is genuinely repeated and the render check confirms it.

2. **Inventory the page**
   - Build a visual inventory: title/subtitle/body text, cards, panels, containers, arrows, connectors, icons, labels, footers, backgrounds.
   - Assign stable IDs to every non-text visual asset, e.g. `process_log_parse`, `output_excel_sheet`, `bottom_human_reviewer`.
   - Record approximate bounding boxes and target visual size for each asset.
   - Mark each non-text visual as either `native_editable` or `imagegen_asset` using the Non-Negotiable Image-Generation Gate above.

3. **Generate icons and visual assets**
   - Use the image generation model for every `imagegen_asset`. Prompt for isolated flat/vector-style assets with no text, no labels, no numbers, no card frame, no shadow unless visible in the reference.
   - For complex visual regions, first analyze the semantic target and prompt the model for a clean rebuilt asset, not a pixel crop copy. Keep text outside the image whenever it can be native editable text in PowerPoint.
   - Prefer generating assets on a transparent background. If alpha is unavailable, generate on a clean removable background, then remove it and repack onto a true transparent RGBA canvas.
   - Asset grids are allowed only with explicit `C×R` alignment rules, where `C` is column count and `R` is row count. This covers square `N×N` grids and rectangular grids such as `5×4`.
   - In the image-generation prompt, state the grid dimensions exactly: `C columns × R rows`, overall canvas ratio `C:R`, equal-size cells, visible or intentionally empty gutters between cells, each icon centered on its own cell center, each icon constrained to the central 55-65% safe zone, and at least 20-25% empty padding inside every cell. Require no clipped edges, no overflow into gutters, and no cross-cell overlap.
   - For square `N×N` grids, request a square canvas and `N` equal rows/columns. For rectangular `C×R` grids, request a canvas whose aspect ratio matches `C:R`. Edge cells must use the same safe-zone and padding rules as interior cells.
   - Each cell must be cut into exactly one semantic asset. Avoid mixing multiple icons into one asset.
   - Do not trust grid math alone. After cutting an asset grid, remove cross-cell fragments and inspect a contact sheet of the final independent PNGs. If any icon contains stray arcs, dots, wedges, clipped strokes, partial marks from adjacent cells, or edge-cell clipping from the generated sheet itself, treat the grid as invalid and regenerate the grid with stricter safe-zone, gutter, and padding constraints before inserting assets into PPT.
   - After cutting, normalize each PNG to a transparent canvas with generous safety padding. Target: at least 10 px transparent edge padding; for 300x300 icons, 40-70 px padding is safer.
   - When inserting into PPT, scale by the asset's non-transparent alpha bounding box, not by the full transparent canvas. This preserves padding without making icons look too small.

4. **Rebuild the PPTX**
   - Use `python-pptx`, PowerPoint automation, or the repo's established PPT tooling.
   - Prefer native slide background fill for plain white/off-white pages (`slide.background.fill`) instead of adding a full-slide white rectangle shape. Only use a bottom background rectangle when it carries visible editable decoration that PowerPoint background fill cannot represent.
   - Use native PowerPoint text boxes for all readable text. Do not rasterize editable text into images.
   - Use native shapes for rounded cards, panels, borders, separator lines, dashed lines, and ordinary arrows.
   - Control PowerPoint rounded rectangles explicitly. `MSO_SHAPE.ROUNDED_RECTANGLE` defaults to huge capsule corners on some aspect ratios; set `shape.adjustments[0]` around `0.025-0.08` and verify in render.
   - Use one generated PNG per icon/complex visual, with transparent background and no clipped edges.
   - Do not stretch icons. Preserve aspect ratio and center by alpha content box.
   - Before writing dense table cells, cards, button labels, and mixed Chinese/English labels, run a text-fit preflight instead of guessing font sizes. Estimate whether the text fits the target bbox at the chosen font size, then adjust within a role-specific range before building the PPTX.
   - Avoid both extremes: do not let text overflow, cross table borders, or force unintended line breaks; also do not shrink text below the visual hierarchy of the reference just to make it fit. If text only fits below the floor size, first widen the text box, reduce margins, adjust column widths, or allow the same wrap pattern as the reference.
   - For Chinese text in `python-pptx`, set the East Asian typeface in OOXML (`a:ea`) as well as `run.font.name`; otherwise PowerPoint may fall back to Songti/serif fonts and shift the layout.
   - Treat repeated label/button components as responsive, not fixed. Mixed English+Chinese labels such as `Agents 工作流` often need a smaller font, wider text box, or adjusted text offset compared with pure Chinese labels.
   - Build tool/example buttons as native button shapes plus one independent icon PNG plus editable text. Do not bake labels such as `Doc`, `PPT`, `frontend`, `imagegen`, or `GitHub` into the icon image.
   - For circular process loops, avoid relying only on curved connectors when the reference uses smooth arc arrows. PowerPoint curved connectors can render as S-shaped bends; use native arc/arrow shapes or editable freeform filled arc arrows when needed.
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
- **Text-fit preflight:** for every dense table cell, card title, button label, and icon-adjacent label, estimate text width/height before generating the PPTX. Prefer a real font metric path such as PIL `ImageFont.truetype()` with Microsoft YaHei/SimHei/Arial when available; otherwise use a conservative CJK-aware approximation (`CJK char ~= 1em`, Latin/digit/punctuation ~= 0.45-0.65em`). Binary-search the largest font size that fits the target bbox with 8-12% horizontal safety padding and the intended max line count. Use this as the initial PPT font size, then still render-check.
- **Role font ranges:** keep sizes within a reference-like range before resorting to layout changes. For a 13.33 in 16:9 slide, typical ranges are: title `34-44 pt`, subtitle `20-26 pt`, question/card title `22-30 pt`, table header `21-26 pt`, table body `14-18 pt`, tool/name labels `14-21 pt`, footnotes `10-13 pt`. If the fit result is below the floor, adjust geometry or wrapping rather than silently accepting tiny text.
- **Overflow guards:** table body text should stay inside its own cell with at least 10-16 px visual padding from vertical grid lines. Card text should reserve icon space first, then fit only in the remaining text area. For one-line reference labels, do not allow accidental wrapping; for multi-line reference labels, match the observed line count and line spacing.
- **Undersize guards:** if fitted text uses less than roughly 65% of the available width and looks visibly smaller than neighboring peer labels, raise the size up to the role maximum or reference estimate. Avoid overcorrecting from overflow into a weak, under-scaled table.
- **Alpha-box image placement:** inspect each transparent PNG's alpha bounding box, fit the visible bbox into the target slot, then offset the full canvas by the bbox left/top. This keeps transparent safety padding without shrinking icons.
- **Content-grid cutting:** for generated asset sheets with outer margins, do not cut by `image_width / C` and `image_height / R` from `(0,0)`. Detect the actual `C×R` content grid first, e.g. with blue-pixel projection runs or another color/alpha mask, verify exactly `C` column bands and `R` row bands, derive row/column centers, compute cell edges from center midpoints, then cut. Save the detected edges and padding failures to a grid alignment report.
- **Rounded rectangles:** after creating `ROUNDED_RECTANGLE`, set `shape.adjustments[0]`; use smaller values for large panels (`0.025-0.04`) and slightly larger values for pills/buttons (`0.06-0.10`).
- **Tool buttons:** compose each button from a native rounded rectangle, `add_picture(icon_id, ...)`, and `add_text(label, ...)`. Tune icon slot, text offset, and font size per label.
- **Wide icon slots:** magnifier, loop, sync, person-loop, and arrow-heavy icons often have a much wider transparent canvas or handle than square symbols. In tight cards, give these icons smaller/lower-left slots or a dedicated variant so both the visible icon and the PPT selection box stay clear of text.
- **Local crop QA:** after rendering, crop suspicious regions with PIL and inspect them separately. Do this before final delivery when a slide has tight labels, right-side tool grids, or bottom feedback bars.
- **Asset manifest proof:** include for every `imagegen_asset` its prompt summary, generated source path when available, final PNG path, and any cleanup/cutting operation. If an asset has no image-generation source, it is not a valid final icon/complex asset.

7. **Validate before delivery**
   - Run the bundled helper:

```bash
python scripts/check_rebuild_assets.py --asset-dir path/to/assets
```

   - Open or inspect the rendered PNG before claiming completion.

## Lessons From Real Repairs

- Prevent icon clipping by requiring the generated grid itself to keep every icon fully inside its own cell, then cut by verified grid cells and repack content into a larger transparent canvas.
- The word "generated" is not enough. A script-drawn PNG is still a hand-authored substitute and violates this skill for icons and complex visuals. Use the image generation model first, then post-process the generated image.
- Asset sheets can leak adjacent-cell fragments into button icons. Treat stray bottom arcs, dots, wedges, or partial marks as a real grid/cutting failure even if the cut asset passes padding checks. Fix the grid prompt, alpha-component cleanup, or recutting logic, then re-render the actual PPT crop.
- Edge cells in a generated icon sheet must have the same safe-zone and padding as interior cells. Do not accept a grid sheet with edge-cell clipping, overflow, or cross-cell overlap.
- Windows Explorer thumbnails may expose edge problems sooner than PPT. Treat any thumbnail clipping as a real asset bug.
- If keying a non-transparent background, do not remove colors that are part of the icon palette. Green-screen cleanup can destroy green icons; checkerboard cleanup can leave gray edges.
- Large flow arrows should be native arrow shapes or connectors. Avoid building arrows from separate rectangles and triangles unless the reference truly requires separate pieces.
- Text fitting must be handled before first render, not only by approximate coordinates. Use a preflight fit with role-specific floors/ceilings, then check the rendered PPT and local crops. Widen boxes, adjust columns, or reduce font size only within the accepted role range when Chinese labels wrap differently in PowerPoint.
- CJK font assignment must survive PowerPoint export. If the render shows serif/Songti-like glyphs, set `a:latin`, `a:ea`, and `a:cs` typefaces in the run XML.
- Reused tag/button components need per-label overrides. If a label mixes English and Chinese, test a local crop and tune `font_size`, `text_offset`, or width before final delivery.
- PowerPoint rounded rectangles can turn into oversized capsules. Always adjust corner radius and render-check large panels, cards, and small tool buttons.
- Right-side tool panels should stay editable: native rounded buttons, generated icon PNGs, and separate text labels.
- Avoid leaving a full-slide white rectangle at the bottom of the selection pane. It usually comes from using a shape as the page background; use native slide background fill for plain backgrounds so the editable object list stays clean.
- Faint decorative rings are easy to overbuild. If the user sees extra gray circles, reduce the number of ellipses, increase transparency, and clear shadows; keep only rings visible in the reference.
- For circular workflows, freeform arc arrows can match the reference better than connector curves while staying editable.
- For rounded dashed feedback loops, first try a single editable open freeform path with PPT native dashed line styling and a native tail arrow. This gives the cleanest selection pane and preserves editability. PowerPoint's built-in connector types are only straight/elbow/curve, so use a freeform path when the loop needs multiple bends. If that renders poorly, fall back to whole native dashed connectors for straight runs and segmented elbows only.
- When an output PPTX is open and locked, write a new versioned filename instead of killing the user's app or overwriting their open file.

## Deliverables

Return the final `.pptx` path plus, when produced:

- Rendered PNG preview.
- `assets/` folder of generated transparent icon PNGs.
- Asset manifest or visual inventory.

Mention any remaining limitation plainly, especially if a complex icon is a generated approximation rather than a perfect vector recreation.
