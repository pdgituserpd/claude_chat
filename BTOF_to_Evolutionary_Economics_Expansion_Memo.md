# From BTOF to evolutionary economics: expansion memo (2 Oct 2026)

Prepared against the Research Audit Handoff of 1 Oct 2026.

## Short answer

The natural next door is neither dynamic capabilities nor organizational learning as a whole. It is the evolutionary theory of the firm that BTOF itself spawned, entered through three doors you already half-stand in: selection (Red Queen and ecology), retention (routines and the internal selection of inventions), and technology-population evolution. Your disk now supports four distinct populations: technologies, firms, inventions, and failure events. The claim that evolutionary economics cannot be run empirically is wrong for your data. What cannot be run is the full Nelson-Winter model as a system, and anything that needs private-firm births.

## 1. Theory: six branches, ordered by distance from your current work

| # | Branch | Core claim | Why it is next for you | Anchors | Watch-outs |
|---|---|---|---|---|---|
| T1 | Evolutionary theory of the firm (Nelson-Winter) | Routines persist; search is triggered by unsatisfactory results and is local; the market selects among the results | Nelson and Winter built directly on Cyert and March. You already study the trigger and the search. The missing legs are selection and retention, which is where every idea below plugs in | Nelson & Winter 1982; Winter 2003 SMJ; Dosi, Nelson & Winter 2000 | Do not try to test the model as a whole. Pick one leg per paper |
| T2 | Red Queen and organizational ecology | Firm-level learning in response to competition aggregates into population-level selection; inertia makes adaptation rare and selection common | The Red Queen is literally BTOF search at the firm level plus ecological selection at the population level. Your duration and vacillation constructs map onto Barnett's "experience with competition" and "competitive hysteresis". Knowledge breadth is a niche-width measure | Barnett & Hansen 1996 SMJ; Barnett 2008; Barnett & Pontikes 2008 Mgmt Sci; Derfus et al. 2008 AMJ; Hannan & Freeman 1984; Dobrev, Kim & Hannan 2001 AJS | Ecology's heart is founding and small-firm mortality, which Compustat never sees. Frame as incumbent populations |
| T3 | Organizational learning, the "interpreting experience" branch only | Feedback is ambiguous; firms learn superstitiously, fall into competency traps, and learn from others' failures | Org learning does have a structure. Levitt & March 1988 split it into learning from direct experience, interpreting experience, organizational memory, and learning from others. BTOF is the search-trigger piece of the first two. P025 is already a superstitious-learning paper; your noise and vacillation work is "ambiguity of feedback". The learning-from-failure sub-branch now has data on your disk | Levitt & March 1988; Levinthal & March 1993 SMJ; Denrell & March 2001 Org Sci; Argote & Miron-Spektor 2011 Org Sci; Baum & Dahlin 2007 Org Sci; Madsen & Desai 2010 AMJ; Kim & Miner 2007 AMJ | Ambidexterity is a sub-branch you have already published in. Do not re-enter via that door |
| T4 | Industry and technology evolution | Technologies and industries pass through fluid, dominant-design, and shakeout phases; incumbents fail at competence-destroying transitions | P023 and P024 are already incumbent-adaptation papers in disguise. The life-cycle stage of a CPC domain is a selection environment you can measure | Klepper 1996 AER; Anderson & Tushman 1990 ASQ; Henderson & Clark 1990; Tripsas 1997; Agarwal & Gort | Needs a defensible domain-stage measure; KPST and AIPD help |
| T5 | Capability lifecycle and resource redeployment | Capabilities are founded, developed, and then retired, retrenched, renewed, replicated, redeployed, or recombined | This is the empirically tractable corner of dynamic capabilities, and it is exactly P023's exit and pipeline #7's localization territory. Zollo & Winter is the explicitly evolutionary DC paper | Helfat & Peteraf 2003 SMJ; Zollo & Winter 2002 Org Sci; Lieberman, Lee & Folta 2017 SMJ; Karim & Mitchell 2000; Karim 2006 SMJ; Girod & Whittington 2017 SMJ | You are right that DC as a construct is unfalsifiable. Position in redeployment and reconfiguration, cite DC as the umbrella in one paragraph, and let the DC people cite you |
| T6 | Fitness landscapes and complexity | Search outcomes depend on the interdependence of a firm's knowledge components and on how fast the landscape moves | Your dynamism and vacillation work is a "moving target" story. Fleming and Sorenson turned patent subclass coupling into an empirical ruggedness measure you can compute from the CPC tables already on disk | Levinthal 1997 Mgmt Sci; Gavetti & Levinthal 2000; Posen & Levinthal 2012 Mgmt Sci; Fleming & Sorenson 2001 RP and 2004 SMJ; Sorenson, Rivkin & Fleming 2006 RP | Mostly simulation literature; the empirical bridge is narrow but well cited |

Near cousins not in the six: path dependence for persistence and lock-in (Sydow, Schreyögg & Koch 2009 AMR), the attention-based view for your 10-K text work (Ocasio 1997), and threat rigidity.

## 2. Data: six branches the disk already supports

| # | Population | What you can build now | Files | Nearest paper | Blockers |
|---|---|---|---|---|---|
| D1 | Technologies (CPC subclass-years) | Density, entries, exits, age, concentration of all patenting organizations per subclass-year. PatentsView covers every assignee, so the population is complete even though DISCERN links only listed firms. Then firm-level domain entry and exit under feedback with domain density, growth, and age as selection-environment moderators | PatentsView g_ tables; DISCERN 2.0; P023 domain spells | "Density dependence of technological domain exit": a domain-level ecology, plus Podolny-Stuart niche crowding via citations | None |
| D2 | Firms | CRSP delisting codes separate merger, liquidation, and dropped exits, so firm exit by mode is measurable, unlike patent exit modes in cut idea #14. TNIC gives population boundaries. Sales-share reallocation within TNIC gives replicator-dynamics tests | Compustat; CRSP monthly to 2021; SDC M&A; TNIC | "Does problemistic search save the firm?": shortfall, then search vs no search, then exit hazard by mode. The head-on adaptation-vs-selection test the feedback literature has not run | Listed firms only; Compustat ends FY2021 locally |
| D3 | Inventions inside the firm | A full variation-selection-retention pipeline: applications are variants, office actions are external selection, maintenance-fee decisions at 3.5, 7.5 and 11.5 years are internal retention decisions, assignments are redeployment by sale. This is Burgelman's 1991 internal selection environment with numbers | PatEx; Office Action; maintenance fees to Sep 2026; assignments; KPSS; DISCERN | "Pruning under pressure": which patents firms let lapse when below aspiration, and whether the selection criteria shift toward core, toward value, or toward age | None. Wall off from A5 and A7 by making retention the DV |
| D4 | Routines | Routine stability proxies: year-over-year textual similarity of 10-K Item 1 and MD&A; self-citation and reuse share; segment adds, drops and recombinations 1976-2020; inventor-team persistence | EDGAR sections; DISCERN citations; Compustat Segments; Harvard inventors to 2010 | "Routine churn under feedback time structure": does vacillation produce churn without direction | PatentsView inventor tables not downloaded, so inventor persistence stops at 2010 |
| D5 | Technological discontinuities | KPST breakthrough and similarity series give a domain-level discontinuity index over time; AIPD gives AI as a specific paradigm shift | KPST; AIPD; DISCERN | Reframe P024 as incumbent response to a competence-destroying discontinuity conditioned on feedback | None |
| D6 | Failure events | Own and rivals' recalls, accidents, inspections and adverse events over long windows. These are the datasets of Baum & Dahlin (railroads), Haunschild & Sullivan (airlines) and Madsen & Desai | NHTSA, FDA, CPSC recalls; FRA; NTSB; BTS; OSHA | Pipeline #10 widened into vicarious learning across the population with your duration and vacillation lens | Name-to-gvkey crosswalks; single-industry samples limit breadth |

A seventh, smaller option is external variation: SDC alliances and M&A to 2019 let you test shortfall against build, borrow, or buy responses, as in Capron and Mitchell and in Kavusan and Frankort's 2019 SMJ behavioral alliance-portfolio paper.

Note on the FIVES folder: the Carroll-Swaminathan breweries, Henderson photolithography, Sorenson workstations, Lieberman chemicals, and Thompson shipbuilding files are the canonical ecology, discontinuity, and learning-curve datasets. They are good for replication pilots and teaching, not for A* novelty.

## 3. Can evolutionary economics be run empirically on your data? Yes, with two real limits

What is genuinely hard is the complete Nelson-Winter model, because routines and search rules are unobserved and the model is a simulation. Nobody estimates it. The history-friendly models of Malerba, Nelson, Orsenigo and Winter are also simulations calibrated to case histories. That is where the "it cannot be done" folklore comes from.

Four empirical traditions of evolutionary economics run on exactly your data:

1. **Industrial dynamics econometrics, Dosi's school.** Persistence of heterogeneity, fat-tailed growth distributions, and replicator-dynamics selection tests of whether market share flows toward fitter firms. Bottazzi, Dosi, Jacoby, Secchi and Tamagni 2010 ICC is the template. Needs a firm panel with sales and a population definition. You have Compustat and TNIC.
2. **Ecology and Red Queen.** Hazard models with density, age, size and competitive experience. Needs dated exit events. You have CRSP delistings, Compustat and SDC.
3. **Technological evolution on patents.** Podolny & Stuart 1995 AJS, Stuart & Podolny 1996 SMJ, Fleming & Sorenson 2001 and 2004, Sorenson, Rivkin & Fleming 2006. All patent-based and ecological or evolutionary in model. You have better data than they had.
4. **Variation-selection-retention at the invention level.** Renewal models exist in economics since Pakes 1986 and Bessen 2008, but no one has given them a behavioral trigger. That gap is yours.

The two real limits:

- **Listed firms only.** Founding and small-firm mortality are invisible in Compustat. Mitigations: define the population as technologies or applications, where PatentsView covers everyone; or claim incumbent adaptation explicitly, which is what Tripsas, Henderson and most SMJ work do anyway. Private-firm dynamics would need Orbis financials or Census data, neither on disk.
- **Routines are unobserved.** Every proxy is contestable. The defense is triangulation across text, citation reuse, inventor persistence and segments.

Smaller limits: Compustat stops at FY2021, IBES at 2018, Office Actions cover 2008-2017, and disambiguated inventors stop at 2010.

## Recommended spine

One bridging claim makes the branch read as a program rather than a scatter: the time structure of performance feedback governs the balance between adaptation and selection. Two papers lead it.

| Paper | Population | Why first | Ceiling (C/E/B) |
|---|---|---|---|
| Does problemistic search save the firm? | Firms (D2) | The feedback literature assumes search is adaptive and never tests survival. Ecology says selection does the work. Posen et al. 2018 Annals flag this as open | 13-14 (3-4 / 2 / 2). Evidence score is capped by selection on unobservables in who searches |
| Pruning under pressure | Inventions (D3) | Discrete, dated retention decisions with the examiner-leniency instrument you already built for P025 | 13-14 (3 / 3 / 1-2) |

Both are data-ready today. D1 is the third, and it inherits P023's builds.
