# Frontend for the B&B Visualization 𖣂

<<<<<<< HEAD
> This code is not important, unless you want to change the visualization
> behavior
=======
> You will not modify this folder, unless you want to change the visualization behavior
>>>>>>> upstream/main

This folder provides the typescript and css files that can be transpiled into
static js and css in `../knapsack_bnb/static`. These files are then used by the
jinja templates in `../knapsack_bnb/templates`.

## Develop locally ⚡

### Installation 💾

```bash
npm i
```

### Build Continously 🏗️

```bash
npm run watch
```

### Generate API types from python backend

```bash
pip install pydantic-to-typescript
python generate_typescript_defs.py
```
