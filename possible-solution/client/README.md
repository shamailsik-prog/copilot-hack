# create-svelte

Everything you need to build a Svelte project, powered by [`create-svelte`](https://github.com/sveltejs/kit/tree/master/packages/create-svelte).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```bash
# create a new project in the current directory
npm create svelte@latest

# create a new project in my-app
npm create svelte@latest my-app
```

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```bash
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```bash
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://kit.svelte.dev/docs/adapters) for your target environment.

## Architecture rules

Import boundaries are enforced by [dependency-cruiser](https://github.com/sverweij/dependency-cruiser).

```bash
npm run depcruise         # validate the rules (non-zero exit on an error)
npm run depcruise:text    # list every edge in the graph
npm run depcruise:graph   # write a Mermaid graph to dependency-graph.mmd
```

The layering the rules describe:

```
src/routes/**        pages and endpoints (+page.svelte, +page.server.ts)
      |
      v
src/lib/index.ts     public surface of the shared layer (the `$lib` alias)
      |
      v
src/lib/**           shared models and helpers
```

Dependencies point downwards only. `src/lib` never imports from `src/routes`, routes
reach the shared layer through the `$lib` barrel rather than deep-importing into it,
routes do not import each other, and server-only modules never reach browser code.

Rules live in [`.dependency-cruiser.js`](./.dependency-cruiser.js), each with a comment
explaining the fix when it trips.

Two notes on the setup:

- `tsconfig.depcruise.json` exists only so the resolver can follow `$lib` and `$app/*`.
  The build still uses `tsconfig.json`; the aliases SvelteKit generates carry no
  `baseUrl`, which dependency-cruiser's resolver requires.
- Type-only imports are tracked in `.ts`/`.js` files, but **not** inside `.svelte`
  files — the Svelte compiler strips types before dependency-cruiser sees the module.
  Value imports in `.svelte` files are tracked normally.

The Flask service in `../server` is Python and is out of scope for this tooling; the
client talks to it over HTTP, not by import.
