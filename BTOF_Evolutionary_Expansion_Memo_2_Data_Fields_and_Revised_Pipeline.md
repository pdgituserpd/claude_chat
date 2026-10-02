# Expansion memo 2: dataset-to-theory map and the revised pipeline (2 Oct 2026)

Companion to `BTOF_to_Evolutionary_Economics_Expansion_Memo.md`.

Correction to memo 1: ambidexterity is not a closed door. March 1991 is itself an evolutionary model of variation and retention, and P014 established that feedback shapes the balance. The evolutionary extension asks what happens to the variants that feedback generates, which is new paper N2 below.

Legend for the evolutionary leg each dataset or paper serves: **V** variation (search, entry, new variants), **Se** external selection (market, examiner, rivals), **Si** internal selection (the firm's own pruning), **R** retention (routines, persistence, carriers), **P** population-level structure (density, boundaries, co-evolution).

## 1. Dataset by dataset: which theory fields each one serves best

Fit = how close the best use sits to your paradigm of time-structured feedback, search, and exit. H high, M medium, L low.

### 1A. Patents and innovation

| Dataset | Fields that carry the theory | Theory fields it serves best, ranked | Leg | Fit |
|---|---|---|---|---|
| DISCERN 2.0 | gvkey-year patent counts, CPC and USPC classes, citations, 1980-2021 | 1 BTOF innovation feedback. 2 Nelson-Winter local search. 3 Capability lifecycle via domain entry and exit. 4 Exploration-exploitation | V, Si | H |
| PatentsView g_ tables, all assignees | cpc_current, cpc_at_issue, citations, assignee ids, grant dates | 1 Organizational ecology of technologies: density, entry, exit per subclass-year across all organizations. 2 Podolny-Stuart technological niches and crowding. 3 Fitness landscapes via subclass coupling, Fleming-Sorenson. 4 Knowledge recombination | P, Se | H |
| PatentsView pre-grant | published applications, cpc_current, 2001 on | 1 Variation-selection-retention at the invention level: pending variants. 2 Real options on abandonment | V, Si | M-H |
| PatEx | application status and status date, examiner, art unit, filing and disposal dates, continuity | 1 External selection and luck: superstitious learning, learning under ambiguity. 2 VSR at the invention level. 3 Identification via examiner leniency for anything downstream | Se, Si | H |
| Office Action dataset, 2008-2017 | rejection type 101/102/103/112 per action, mail dates | 1 Content of the selection signal: diagnostic learning, interpretation of experience. 2 Attribution | Se | M, window-limited |
| AIPD 2023 | AI component scores per patent and PGPub | 1 Technological discontinuities and incumbent adaptation. 2 Dominant-design emergence. 3 Vicarious learning from peers' entry | V, P | M-H |
| Patent Assignments | reassignment events, parties, dates, conveyance type | 1 Resource redeployment and markets for technology. 2 Capability retirement vs redeployment. 3 Enforcement and appropriation | Si, R | H for T5 |
| Maintenance fee events | renewal and lapse at each stage, to Sep 2026 | 1 Internal selection environment, Burgelman. 2 Retention decisions under feedback. 3 Patent renewal models, Pakes | Si, R | H |
| KPSS 2025 | market value per patent, permno | 1 Fitness measured by value rather than count. 2 Selection on value: which variants the market rewards. 3 Value vs volume aspirations | Se | H |
| KPST | similarity, importance, breakthrough, pairwise citations | 1 Technological discontinuities and creative destruction at scale. 2 Recombinant novelty and landscapes. 3 Dominant-design timing per domain | P, V | H |
| NBER and Harvard inventors, to 2010 | disambiguated inventors, teams, mobility | 1 Carriers of routines: retention and inheritance of knowledge. 2 Structural ambidexterity via network modularity. 3 Nested aspirations | R, V | H but truncated at 2010 |
| ORBIS Patent | BvD ids, global assignees | International and private-firm patenting populations. No financials, so limited | P | L until Orbis financials |
| Reliance on Science, lookups only | paper-to-patent links | Science-technology linkage, absorptive capacity | V | L until the main file is on disk |

### 1B. Financial, market and governance

| Dataset | Fields that carry the theory | Theory fields it serves best, ranked | Leg | Fit |
|---|---|---|---|---|
| Compustat Fundamentals, to FY2021 | ROA, sales, R&D, capex, SG&A, inventories, leverage, employees, deletion reason | 1 BTOF financial aspirations. 2 Industrial dynamics: growth-rate distributions, persistence of heterogeneity, replicator dynamics. 3 Ecology survival models. 4 Strategic change | V, Se, P | H |
| Compustat Segments, 1976-2020 | segment sales, assets, capex, R&D by business and geography; segment adds and drops | 1 Capability lifecycle and redeployment across units. 2 Internal selection across businesses, Burgelman. 3 Shortfall localization. 4 Diversification | Si, R | H |
| CRSP monthly with delisting codes | returns, volatility, dlstcd for merger, liquidation, dropped | 1 Selection with exit mode: ecology and Red Queen. 2 Market-based fitness and drawdowns. 3 Behavioral agency | Se, P | H |
| BoardEx, to 2021 | executives, directors, tenure, prior roles, interlocks | 1 Upper echelons and inertia via tenure. 2 Vicarious learning through interlocks. 3 Behavioral agency | R | M, paradigm-adjacent |
| IBES, to 2018 | consensus forecasts, actuals, dispersion | 1 Expectations as aspirations. 2 Capital-market selection pressure. 3 Attention | Se | M, partial |
| Worldscope, 1980-2019 | global fundamentals | Cross-country replication, institutional context | - | L-M |
| Diversification data, 1980-2017 | product and geographic diversification by ISIN | Redeployment and scope decisions | Si | M |
| CEO dismissal, to 2018 | forced turnover, dates | 1 Internal selection of the decision maker. 2 Success bias, Barnett-Pontikes | Si | M |
| KLD, Asset4 | CSR strengths and concerns, ESG scores | Multiple goals, stakeholder aspirations, institutional pressure | - | L-M |
| LIVA, 1999-2019 | long-term value creation | Long-horizon fitness; selection outcomes | Se | M |

### 1C. Deals, text, industry, macro

| Dataset | Fields that carry the theory | Theory fields it serves best, ranked | Leg | Fit |
|---|---|---|---|---|
| SDC alliances, to 2019, gvkey-linked | partners, new vs repeat, type, dates | 1 Borrowed variation and build-borrow-buy. 2 Alliance portfolio reconfiguration as a behavioral response, Kavusan-Frankort 2019. 3 Social referents | V, R | H |
| SDC M&A, 1980-2019 | acquisitions, divestitures, targets | 1 Exit by acquisition as a selection mode. 2 Buy as an alternative to search. 3 Redeployment | Se, Si | H |
| EDGAR 10-K sections, Items 1, 1A, 7, 7A | business description, risk factors, MD&A, market risk, gvkey-year panel 1993-2021 | 1 Attention-based view and attribution. 2 Routine stability via year-over-year textual change. 3 Major-customer disclosures, which partly unblock A2. 4 Sensemaking of feedback | R, V | H |
| AnnualReports.com PDFs, A-R only | shareholder letters | Impression management and attribution; no gvkey link | - | L until linked |
| Loughran-McDonald | tone dictionaries | Supportive for attribution and sentiment | - | support |
| Hoberg-Phillips TNIC, 1988-2023 | pairwise similarity, dynamic peer sets | 1 Population boundaries for ecology and Red Queen. 2 Social aspiration referents. 3 Niche overlap and crowding. 4 Market categories | P, Se | H |
| ALP concordances | patent class to industry | Selection environment per technology domain | P | support |
| Economic Policy Uncertainty | US, global, daily | Moving-target environments, real options | - | support |
| Hassan political risk, 2002-2021 | firm-quarter political risk | Non-market strategy; a moderator at most | - | L |
| Sautner climate exposure, to 2024 | firm-quarter climate exposure | Multiple goals; environmental aspirations | - | L-M |
| Felten AI exposure | industry and occupation AI exposure | Discontinuity exposure for P024 | P | M |
| NBER-CES, to 2011 | industry shipments, productivity, prices | Industry selection environment; shift-share shocks | Se, P | M |

### 1D. Regulatory, safety, failure, science

| Dataset | Fields that carry the theory | Theory fields it serves best, ranked | Leg | Fit |
|---|---|---|---|---|
| NHTSA recalls and complaints | recall dates, components, complaint counts | 1 Learning from failure, own and others'. 2 Reliability routines | Se, R | M-H, needs name match |
| EPA TRI, 1987-2024, gvkey match to 2014 | facility releases by chemical | Multiple goals, environmental aspirations, institutional pressure | - | M |
| EPA ECHO | enforcement cases | Regulatory selection pressure | Se | L-M |
| FRA rail accidents, NTSB, BTS on-time | accidents, incidents, delays by carrier and date | 1 Learning from failure: the Baum-Dahlin and Haunschild-Sullivan datasets. 2 Vicarious learning across a population | Se, R, P | M-H |
| FDA recalls, adverse events, approvals, complete response letters, Orange Book | product failures, rejections, approvals by firm and date | 1 External selection signals in pharma: a CRL is a rejection letter with content, like an office action. 2 Learning from failure. 3 Diagnostic feedback | Se | M-H |
| ClinicalTrials.gov industry studies | trial starts, terminations, phases | VSR in pharma: trial termination is internal selection of pipeline variants | V, Si | M-H |
| OSHA, MSHA | inspections, violations, injuries | Safety learning, regulatory pressure | Se | L-M |
| EIA-860/923 | plant-level capacity and generation | Utility industry ecology and capacity learning | P | L |
| NIH RePORTER, CORDIS, OpenAlex | grants with patent links, publications by company | Science-technology linkage; public funding as an external variation source | V | M |
| SEC comment letters, 2024-2026, gvkey | letters by filer | External scrutiny; too short a window | Se | L |
| PTAB tables | validity challenges | Narrow substitute for litigation in A3 | Se | M |
| FIVES: breweries, photolithography, workstations, chemicals, shipbuilding | canonical ecology, discontinuity, learning-curve data | Replication pilots and teaching, not A* novelty | - | pilot |
| HCCP Korea, World Management Survey | practices, management quality | Routines and management quality; off-paradigm | R | L |

### 1E. Ranking of theory fields by how well your data support them

1. **Variation-selection-retention at the invention and domain level.** DISCERN, PatentsView, PatEx, pre-grant, Office Actions, maintenance fees, assignments, KPSS. The deepest stack you own, and nobody has put a behavioral trigger on it.
2. **Organizational ecology and Red Queen.** Compustat, CRSP delistings, TNIC, SDC M&A, plus population counts from PatentsView. Complete for incumbents, blind to births.
3. **Capability lifecycle and resource redeployment.** Segments, assignments, SDC, DISCERN domain spells. All linked by gvkey.
4. **Exploration-exploitation and ambidexterity, re-entered through retention.** DISCERN, PatentsView, inventors. Same stack as item 1 viewed from March 1991.
5. **Technology evolution and discontinuities.** KPST, AIPD, PatentsView, Felten.
6. **Organizational learning from failure and under ambiguity.** PatEx for ambiguity; the recall, accident and FDA batch for failure. Strong once crosswalks exist.
7. **Attention-based view and interpretation.** EDGAR sections, Loughran-McDonald.
8. **Fitness landscapes and complexity.** PatentsView CPC coupling, EPU. Narrow but clean.
9. **Upper echelons and behavioral agency.** BoardEx, CEO dismissal. Supported but off-paradigm.
10. **Multiple goals and stakeholders.** TRI, KLD, Sautner. Weakest fit.

## 2. The revised pipeline under the evolutionary outlook

Scores are suggested revisions on your 3C+E+B scale, as ceilings. "Old" is your 30 Sep score where you gave one.

### 2A. The 20-paper pipeline, revisited

| # | Paper | Leg | What changes under the new outlook | Old → suggested | Action |
|---|---|---|---|---|---|
| 1 | AI as exploration domain, P024 | V, P | Reframe as incumbent adaptation to a discontinuity under feedback. Add ML-domain density from PatentsView as a second moderator: entry should rise with density through legitimation, then flatten through competition. Peer evidence then becomes one of two population signals | A-/A → 10-11 | Write now with the density moderator. Still A, but a cleaner story |
| 2 | Input vs output search | V, Se | Reframe as gross variation drawn on vs variation that survives to output. Merge with A5 so that pending-application abandonment is the middle step | 11/7 → 12 as the merged paper | Merge into A5 |
| 3 | Unearned feedback, P025 | Se | Already an evolutionary paper: selection on a noisy fitness signal, superstitious learning. Add the good-luck vs bad-luck asymmetry test | 9 → 12-13 with the asymmetry test | Rebuild on the audited Data Center, then add the test |
| 4 | Mean vs rank aspirations | Se | Rank-based referents are tournament selection; mean-based are proportional selection. Interesting but owned by Denrell | 7-8 | Stays shelved as an appendix |
| 5 | Attribution language | V | Attribution decides whether a shortfall generates variation at all. Keep the ABV frame; evolutionary reading adds one sentence, not a new paper | 11/8 → 11 | Keep, data-ready |
| 6 | Alliance portfolio as referent | V, R | Reframe as borrowed variation: shortfall and new-partner vs repeat-partner formation. Kavusan and Frankort 2019 already did portfolio reconfiguration under feedback, so the referent angle is the only new part | 7-10 → 8 | Keep in the later menu |
| 7 | Shortfall localization | Si, R | Now reads as internal selection across business units, Burgelman, with redeployment of attention and resources from the failing segment. This strengthens, not changes, the job-talk paper | 12 → 13 | Keep as the job-talk paper. Add one hypothesis on whether redeployed search targets the failing segment's classes or the healthy ones |
| 8 | Review: time in performance feedback | - | Widen the pitch to time in feedback and the adaptation-selection balance, bridging BTOF to evolutionary theory. A bridge review is more Annals-shaped than a within-literature review | - | Keep, repitch |
| 9 | Search reversibility | V, R | Irreversible search is lock-in. Path dependence gives the retention side; real options gives the variation side | 13 → 13 | Waits on P017; can be built now |
| 10 | Temporal texture of failure | Se, R, P | Widen from own recalls to population-level vicarious learning using the FRA, NTSB, BTS and FDA files. The Baum-Dahlin design with your duration and vacillation constructs | 8 → 10 | Later menu, higher than before. Needs name crosswalks |
| 11 | Second-order feedback, P026 | R | Learning about search rules is Zollo-Winter deliberate learning. The reframe does not rescue a result that failed twice | parked | Stays parked |
| 12 | Value vs volume | Se | Fitness by value vs count. Folded into P025 | folded | Stays folded |
| 13 | Rival moves as feedback | P, Se | Revive as Red Queen in technology space: rivals' entry into the firm's core subclasses as competitive experience, firm response, and rival counter-response, with TNIC peers. No text similarity needed; CPC overlap suffices | cut 4-7 → 9-11 | Revive as a candidate, N6 |
| 14 | Population-of-technologies selection | P, Si | Revive without exit modes: density dependence of domain entry and exit, domain age and growth as selection environment | cut → 11-13 | Revive as N4 |
| 15 | Drawdown feedback | Se | Performance peak as a retention anchor. Unchanged | 9-12 | Later menu |
| 16 | Aspiration bands | Se | Unchanged | 13 | Waits on P017 |
| 17 | Feedback and inventor retention | R | Inventors as carriers of routines; retention of carriers under shortfall. The VSR frame raises the ceiling | 5-8 → 9-11 | Blocked until PatentsView inventor tables are downloaded |
| 18 | Financial vs environmental goals | - | No evolutionary gain | 8 | Later menu |
| 19 | Political arena | - | Already done | cut | Stays cut |
| 20 | Feedback texture and CEO dismissal | Si | Dismissal is internal selection of the decision maker. Better as a mechanism inside N1 than as its own paper | cut | Stays cut; reuse as a mediator in N1 |

### 2B. The 10 A* ideas, revisited

| # | Idea | Leg | What changes under the new outlook | Old → suggested | Status |
|---|---|---|---|---|---|
| A1 | Structural separation as a switch | V, R | This is structural ambidexterity read as an internal ecology: separated units are protected variation. The evolutionary frame is the natural home | 14 → 14 | Blocked on inventor tables |
| A2 | Transmitted feedback | P | Co-evolution of supplier and customer populations. Partly unblocked: major-customer disclosures sit in Item 1 of the 10-Ks you now have split | 14 → 14 | Partly unblocked via 10-K Item 1 parsing |
| A3 | From search to enforcement | Se, Si | Appropriation as the alternative to variation. PTAB tables are the on-disk substitute | 14 → 14 | Partly blocked |
| A4 | Symbolic gap-closing | V | Pseudo-variation: variation in the signal, not the substance. The strongest paper against the count-based literature, including your own | 14-17 → 14-17 | Partial data |
| A5 | Exploration as the first casualty | V, Si | Merge with pipeline #2 to give gross, pending, and net search in one design. Abandonment of pending exploratory applications is internal selection | 14 → 14 | Ready; absorbs #2 |
| A6 | Diagnostic feedback | Se | The content of the selection signal. FDA complete response letters are a second setting for the same design | 13 → 13 | Ready, 2008-2017 window |
| A7 | Barbell reallocation | V, Si | Where on the distance spectrum variation is kept vs cut, at a point in time. Wall off from N2, which follows variants over time | 13-14 → 13-14 | Ready |
| A8 | Nested aspirations | V | Unchanged | 13 → 13 | Blocked on inventor tables |
| A9 | Symptomatic termination | Se | Selection-pressure relief ends variation. Unchanged | 13 → 13 | Partial; build shocks from Compustat |
| A10 | Search by substitution | V, R | Variation through new carriers vs mutation of existing carriers. Unchanged | 13-14 → 13-14 | Blocked on inventor tables |

### 2C. New papers the outlook adds

| # | Paper | Leg | IV | DV | Moderator or identification | Data | Suggested score | Notes |
|---|---|---|---|---|---|---|---|---|
| N1 | Does problemistic search save the firm? | Se | Shortfall, then search response vs no response | Exit hazard by mode: merger, liquidation, dropped | Industry turbulence; CEO dismissal as mediator. Identification is the weak point: who searches is endogenous | Compustat, CRSP, DISCERN, TNIC, SDC | 13-14 (3-4/2/2) | The head-on adaptation-vs-selection test the feedback literature has not run. Posen et al. 2018 Annals list it as open |
| N2 | Are problem-born explorations kept? | V, R | Birth condition of each technological domain: entered under shortfall vs under surplus or neutral feedback | Survival of the domain in the firm's portfolio; time to exit; growth of output in it | Breadth; initial commitment; feedback after entry. Wall off from A7 by design: A7 is cross-sectional pattern, N2 is longitudinal fate | P023 domain spells, DISCERN, P014 ambidexterity builds | 14 (3-4/3/2) | The ambidexterity re-entry. P014 showed feedback changes the exploration mix; N2 asks whether the exploration born of pressure is retained or pruned. Ready now |
| N3 | Pruning under pressure | Si, R | Shortfall, instrumented by examiner leniency as in P025 | Maintenance-fee lapse at each stage; which patents lapse by distance from core, KPSS value, and age | Portfolio slack; pipeline age | Maintenance fees, PatEx, DISCERN, KPSS | 13-14 (3/3/1-2) | Internal selection with discrete dated decisions. Ready now |
| N4 | Density dependence of technological domain exit | P, Si | Domain density, growth, and age from all patenting organizations | Firm-level domain exit and entry | Firm shortfall as the behavioral trigger interacting with the population signal | PatentsView, DISCERN, P023 spells | 11-13 (3/3/1) | Revives pipeline #14 without exit modes. Ready now |
| N5 | Routine churn under vacillation | R | Vacillation frequency and scale | Year-over-year textual change in 10-K Item 1 and MD&A; segment adds and drops; self-citation share | Breadth; slack | EDGAR sections, Segments, DISCERN | 10-12 (3/2/1-2) | Tests whether vacillation produces change without direction. Text measure needs validation against known reorganizations |
| N6 | Red Queen in technology space | P, Se | Rivals' entry into the firm's core subclasses | Firm response: deepening, exit, or counter-entry; rivals' counter-response | TNIC proximity; firm feedback state | PatentsView, DISCERN, TNIC | 9-11 (2-3/3/1) | Revives pipeline #13. Lower contribution because Barnett's mechanism is known; the technology-space setting is the novelty |
| N7 | Does feedback-driven search speed market selection? | P, Se | Share of firms in a TNIC population responding to shortfall with search | Replicator-dynamics coefficient: share reallocation toward higher-value firms | Population turbulence | Compustat, TNIC, KPSS | 10-12 (3/2/1) | Dosi-school design. Better for SMJ or ICC than AMJ. Reservoir |

### 2D. Revised priority order

Ranked by suggested score, then readiness, with the 31 Jan 2027 and Aug 2027 dates in mind.

| Rank | Paper | Score | Ready | Role |
|---|---|---|---|---|
| 1 | N2 Are problem-born explorations kept? | 14 | Yes | First evolutionary paper. Builds on P014 and P023 builds; closest to your strengths |
| 2 | A4 Symbolic gap-closing | 14-17 | Partial | Highest ceiling. Download PatEx transactions and PatentsView claims |
| 3 | A5 + #2 Gross, pending and net search | 14 | Yes | Variation-selection in one design |
| 4 | #7 Shortfall localization | 13 | Yes | Job-talk paper, now with the internal-selection frame |
| 5 | N3 Pruning under pressure | 13-14 | Yes | Internal selection; reuses the P025 instrument |
| 6 | N1 Does problemistic search save the firm? | 13-14 | Yes | The program's headline question. Build after N2 so the two papers share a story |
| 7 | A7 Barbell reallocation | 13-14 | Yes | Pair with N2 |
| 8 | A6 Diagnostic feedback | 13 | Yes | Window-limited |
| 9 | #9, #16 Reversibility, bands | 13 | Build now | Wait on the SO decision for P017 to submit |
| 10 | N4 Density dependence of domain exit | 11-13 | Yes | Population-level complement to P023 |
| 11 | A1, A8, A10, #17 | 13-14 | Blocked | One free PatentsView download unlocks all four |
| 12 | P024, P025 | 10-13 | In progress | Finish and submit as A papers |

Cut or parked, unchanged: #4, #11, #12, #19, #20. Later menu: #6, #10, #15, #18, A2, A3, A9, N5, N6, N7.

### 2E. What the program looks like as a sentence

The time structure of performance feedback governs how much variation a firm generates, which of that variation it keeps, and whether keeping it helps the firm survive. Papers already done cover generation. N2, N3, A5 and A7 cover internal selection and retention. N1 and N4 cover external selection and the population. That is the arc for the job talk and the tenure statement.
