/** @type {import('dependency-cruiser').IConfiguration} */
export default {
  /*
   * Architecture rules for the SvelteKit client in `possible-solution/client`.
   *
   * The layering this codebase actually has:
   *
   *   src/routes/**   presentation + endpoint layer (+page.svelte, +page.server.ts)
   *         |
   *         v
   *   src/lib/index.ts   public surface of the shared layer (the `$lib` alias)
   *         |
   *         v
   *   src/lib/**      shared models and helpers (models.ts, ...)
   *
   * Dependencies point downwards only. `src/lib` never reaches back up into a
   * route, and a route reaches the shared layer through the `$lib` barrel rather
   * than by deep-importing a module inside it.
   *
   * Note: the Flask service in `possible-solution/server` is Python and is not in
   * scope for dependency-cruiser; it is reached over HTTP, not by import.
   */
  forbidden: [
    {
      name: 'no-circular',
      severity: 'error',
      comment:
        'This module is part of an import cycle. `src/lib/index.ts` is a barrel that re-exports ' +
        './models, so a cycle is one careless import away: a module inside src/lib that imports ' +
        'from "$lib" (instead of the sibling file directly) closes the loop. Import the concrete ' +
        'sibling module from inside src/lib, and reserve "$lib" for consumers in src/routes.',
      from: {},
      to: { circular: true },
    },
    {
      name: 'lib-not-to-routes',
      severity: 'error',
      comment:
        'Something in src/lib imports from src/routes. src/lib is the lower, route-agnostic layer ' +
        'and must stay independently reusable; routes sit above it. Move the shared code down into ' +
        'src/lib and let the route import it, rather than pointing the shared layer at a page.',
      from: { path: '^src/lib/' },
      to: { path: '^src/routes/' },
    },
    {
      name: 'routes-through-lib-barrel',
      severity: 'warn',
      comment:
        'A route deep-imports a module inside src/lib instead of going through the `$lib` barrel ' +
        '(src/lib/index.ts). Keeping routes on the barrel keeps the shared layer free to reorganise ' +
        'its internals. Import from "$lib" and re-export the symbol from src/lib/index.ts if needed. ' +
        '(src/lib/server is exempt: SvelteKit deliberately gives server-only code no barrel, so it ' +
        'is always deep-imported as "$lib/server/...".)',
      from: { path: '^src/routes/' },
      to: {
        path: '^src/lib/',
        pathNot: ['^src/lib/index\\.(?:js|ts)$', '^src/lib/server/'],
      },
    },
    {
      name: 'no-cross-route-imports',
      severity: 'error',
      comment:
        'One route imports a module belonging to a different route. Routes are siblings, not a ' +
        'hierarchy: code shared by two routes belongs in src/lib. (Only one route exists today — ' +
        'this rule is what keeps that from quietly changing.)',
      from: { path: '^src/routes/([^/]+)/' },
      to: {
        path: '^src/routes/([^/]+)/',
        pathNot: '^src/routes/$1/',
      },
    },
    {
      name: 'no-server-only-in-client',
      severity: 'error',
      comment:
        'A module that ships to the browser imports server-only code (a `*.server.ts` module or ' +
        'anything under src/lib/server). SvelteKit refuses to bundle this, and if it ever did it ' +
        'would leak server internals to the client. Pass the data through the `load` function or ' +
        'form action in +page.server.ts instead.',
      from: {
        path: '^src/',
        pathNot: '(?:\\.server\\.(?:js|ts)$|^src/lib/server/|^src/hooks\\.server\\.(?:js|ts)$)',
      },
      to: {
        path: '(?:\\.server\\.(?:js|ts)$|^src/lib/server/)',
      },
    },
    {
      name: 'no-orphans',
      severity: 'warn',
      comment:
        'This module is not imported by anything and imports nothing reachable — likely dead code ' +
        'left behind by a refactor. Ambient type declarations, config files and SvelteKit route ' +
        'entry points are excluded below because they are entered by tooling, not by an import.',
      from: {
        orphan: true,
        pathNot: [
          '(^|/)\\.[^/]+\\.(?:js|cjs|mjs|ts|json)$', // dot files
          '\\.d\\.ts$', // TypeScript declarations (src/app.d.ts)
          '(^|/)tsconfig\\.json$',
          '(^|/)(?:svelte|vite)\\.config\\.(?:js|ts)$',
          '^src/routes/', // SvelteKit invokes route files by convention
        ],
      },
      to: {},
    },
    {
      name: 'not-to-unresolvable',
      severity: 'error',
      comment:
        'This module depends on something that cannot be resolved on disk — either the dependency is ' +
        'missing from package.json, or the path is wrong. `$lib` and `$app/*` are mapped in ' +
        'tsconfig.depcruise.json; `./$types` is exempt because SvelteKit synthesises it into ' +
        '.svelte-kit/types via tsconfig `rootDirs`, which this resolver does not implement.',
      from: {},
      to: {
        couldNotResolve: true,
        pathNot: '(?:^|/)\\$types$',
      },
    },
    {
      name: 'not-to-unlisted-npm-dep',
      severity: 'error',
      comment:
        'This module imports an npm package that is not declared in package.json. It works locally ' +
        'only by accident of hoisting and will break on a clean install. Add it as an explicit ' +
        'dependency. (@sveltejs/kit is exempt: `$app/*` is aliased straight into the package\'s ' +
        'src/runtime, bypassing its export map, so the resolver cannot tie it back to the manifest ' +
        'entry — the package is declared.)',
      from: {},
      to: {
        dependencyTypes: ['npm-no-pkg', 'npm-unknown'],
        pathNot: 'node_modules/@sveltejs/kit/',
      },
    },
    {
      name: 'no-duplicate-dep-types',
      severity: 'warn',
      comment:
        'This dependency is declared more than once in package.json (e.g. in both dependencies and ' +
        'devDependencies). Pick one section.',
      from: {},
      to: {
        moreThanOneDependencyType: true,
        dependencyTypesNot: ['type-only'],
      },
    },
    {
      name: 'no-deprecated-core',
      severity: 'error',
      comment:
        'This module depends on a deprecated Node core module. Find the modern replacement before ' +
        'the next Node upgrade removes it.',
      from: {},
      to: {
        dependencyTypes: ['core'],
        path: '^(?:punycode|domain|constants|sys|_linklist|_stream_wrap)$',
      },
    },
  ],

  options: {
    /*
     * Resolve the `$lib` alias. Deliberately NOT ./tsconfig.json: that extends the
     * SvelteKit-generated .svelte-kit/tsconfig.json, whose `paths` carry no
     * `baseUrl`, and dependency-cruiser's resolver needs one — with the build
     * tsconfig every `$lib/...` import comes back unresolvable and the layering
     * rules below silently pass. tsconfig.depcruise.json restates the same two
     * aliases against an explicit baseUrl. See the comment in that file.
     */
    tsConfig: { fileName: 'tsconfig.depcruise.json' },

    /*
     * Track type-only imports (`import type { X } from '...'`). Without this, a
     * layering rule can be dodged simply by importing a type, and the rules above
     * would pass vacuously.
     *
     * KNOWN GAP: this works for .ts/.js modules but NOT inside .svelte files.
     * dependency-cruiser hands .svelte to the Svelte 5 compiler, which strips
     * TypeScript types before dependency-cruiser ever parses the output — so the
     * `import type { Airport } from '$lib'` in src/routes/+page.svelte does not
     * appear in the graph today. Value-level imports in .svelte files ARE seen.
     * Until that gap closes upstream, the layering rules are fully enforced on
     * .ts/.js and enforced only for value imports on .svelte.
     */
    tsPreCompilationDeps: true,

    doNotFollow: { path: 'node_modules' },

    /* Generated by `svelte-kit sync`, and static assets are not modules. */
    exclude: { path: '(?:^|/)(?:\\.svelte-kit|static|build)/' },

    enhancedResolveOptions: {
      /* .svelte must be listed explicitly; it is not a default resolver extension. */
      extensions: ['.js', '.mjs', '.cjs', '.ts', '.mts', '.cts', '.svelte', '.json'],
      exportsFields: ['exports'],
      conditionNames: ['import', 'require', 'node', 'default', 'types'],
      mainFields: ['module', 'main', 'types', 'typings'],
    },

    reporterOptions: {
      dot: { collapsePattern: 'node_modules/(?:@[^/]+/[^/]+|[^/]+)' },
      archi: {
        collapsePattern:
          '^src/lib/[^/]+|^src/routes/[^/]+|^src/[^/]+|^node_modules/(?:@[^/]+/[^/]+|[^/]+)',
      },
    },
  },
};
