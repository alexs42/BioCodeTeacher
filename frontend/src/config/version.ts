/**
 * BioCodeTeacher version and changelog.
 *
 * Version scheme: increment 0.01 for small changes, 0.1 for big ones.
 */

export const APP_VERSION = '0.45'

export interface ChangelogEntry {
  version: string
  date: string
  changes: string[]
}

export const CHANGELOG: ChangelogEntry[] = [
  {
    version: '0.45',
    date: '2026-04-03',
    changes: [
      'Public release preparation: CC BY-NC 4.0 license with AS-IS disclaimer',
      'Version synchronization across all config files',
      'Documentation and metadata cleanup for open-source distribution',
    ],
  },
  {
    version: '0.44',
    date: '2026-04-02',
    changes: [
      'Chat now includes repo architecture context, file summaries, and pipeline stage awareness',
      'Documentation search: auto-fetches API docs for Scanpy, AnnData, Squidpy, and 17 other libraries',
      'Enhanced CHAT_SYSTEM prompt with architecture and documentation awareness',
    ],
  },
  {
    version: '0.43',
    date: '2026-04-01',
    changes: [
      'Chat panel opens by default — no expand click required',
      'New educational prompt suggestions: Teach me this repo, Critique this code, Tutorial mode',
      'Build script: detect versioned Python binaries (python3.13, python3.12, etc.) on macOS/Linux',
    ],
  },
  {
    version: '0.42',
    date: '2026-03-31',
    changes: [
      'Cross-platform macOS build (.app bundle + .dmg installer)',
      'Splash screen with version info and license',
      'Code review fixes: timezone-aware staleness detection, Azure ZDR model plumbing',
      'Bug fix: "de" keyword false positives in architecture agent',
      'Theme fixes: 16 hardcoded Tailwind grays replaced with CSS variables',
      'Header hardcoded rgba values replaced with theme-aware variables',
      'New bio schema fields: pipeline_stage, domain, biological_decisions',
      'Prompt fix: literal %% in format strings',
    ],
  },
  {
    version: '0.41',
    date: '2026-03-28',
    changes: [
      'Initial BioCodeTeacher fork from CodeTeacher',
      'Bioinformatics educator persona for all AI prompts',
      'Architecture agent: Snakemake, Nextflow, nf-core, Cell Ranger, R/Bioconductor detection',
      '30+ bioinformatics file formats (.h5ad, .fasta, .vcf, .smk, .nf, etc.)',
      '"Research Lab" visual theme (teal/indigo, fluorescence microscopy aesthetic)',
      'Provider routing and Azure ZDR model support',
    ],
  },
]
