extraction_prompt = """
Extract ALL content from this page and CLASSIFY by content type.

CONTENT TYPES:
1. **text** - Regular paragraphs, sentences, narrative text, lists, mixed text with numbers
2. **equation** - Mathematical formulas, chemical equations, symbolic expressions
3. **table** - Tabular data with rows/columns (preserve complete structure)
4. **image_definition** - Image captions, figure descriptions, diagram explanations

CRITICAL GROUPING RULES:
1. **MERGE CONSECUTIVE TEXT**: Combine ALL consecutive paragraphs/text into ONE text block
2. **NEW BLOCK ONLY WHEN TYPE CHANGES**: Create new block when switching between text/table/equation/image
3. **KEEP SPECIAL CONTENT INTACT**: Each table, equation, or image gets its own block

Example of CORRECT grouping:
- Running text (paragraphs 1, 2, 3) → ONE text block
- Then table appears → NEW table block
- Then more text (paragraphs 4, 5) → ONE text block
- Then equation → NEW equation block

EXTRACTION RULES:
- Maintain reading order (top to bottom, left to right)
- For TEXT: Merge ALL consecutive paragraphs into single block
- For TABLES: Extract entire table as one block, preserve structure
- For EQUATIONS: Keep complete formula/expression together
- For IMAGES: Describe visual content + extract any embedded text

Return JSON ARRAY format:
[
  {
    "content": "extracted content here...",
    "data_type": "text"
  },
  {
    "content": "formula or equation here...",
    "data_type": "equation"
  },
  {
    "content": "complete table with structure...",
    "data_type": "table"
  },
  {
    "content": "image description here...",
    "data_type": "image_definition"
  }
]

EXAMPLES:

Example 1 - Mixed content page (CORRECT - text grouped):
[
  {
    "content": "The human digestive system is a complex network of organs. It begins with the mouth where mechanical and chemical digestion starts. The mouth contains teeth, tongue, and salivary glands that work together to break down food.",
    "data_type": "text"
  },
  {
    "content": "Table: Digestive Enzymes\\nEnzyme | Location | Function\\nAmylase | Mouth | Breaks down starch\\nPepsin | Stomach | Digests proteins\\nLipase | Small intestine | Breaks down fats",
    "data_type": "table"
  },
  {
    "content": "The process continues in the stomach where HCl is secreted. The stomach is a muscular organ that mixes food with digestive juices. From there, food moves to the small intestine.",
    "data_type": "text"
  }
]

Example 2 - With equations (CORRECT - text grouped):
[
  {
    "content": "Einstein's theory of relativity introduced a fundamental relationship between energy and mass. This groundbreaking discovery changed our understanding of physics.",
    "data_type": "text"
  },
  {
    "content": "E = mc²",
    "data_type": "equation"
  },
  {
    "content": "where E is energy, m is mass, and c is the speed of light. This equation shows that mass and energy are interchangeable.",
    "data_type": "text"
  }
]

Example 3 - Multiple consecutive text paragraphs (CORRECT - merged):
[
  {
    "content": "The retina is the light-sensitive layer at the back of the eye. It contains millions of photoreceptor cells called rods and cones. Rods are responsible for vision in low light conditions. Cones detect color and fine detail. The retina also contains other specialized cells that process visual information.",
    "data_type": "text"
  },
  {
    "content": "Figure 1: Cross-sectional diagram of the human retina showing the photoreceptor layer with rods and cones, the bipolar cell layer, and the ganglion cell layer.",
    "data_type": "image_definition"
  },
  {
    "content": "Retinal diseases can cause vision loss. Common conditions include diabetic retinopathy and macular degeneration.",
    "data_type": "text"
  }
]

IMPORTANT:
- Return ONLY valid JSON array
- Do NOT wrap in markdown code blocks
- Each content block should be complete and meaningful
- Preserve ALL information from the page
"""