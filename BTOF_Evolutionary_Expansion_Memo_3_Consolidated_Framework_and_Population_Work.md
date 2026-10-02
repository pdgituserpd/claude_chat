# Expansion memo 3: the consolidated evolutionary framework, and population-level work (2 Oct 2026)

Companion to memos 1 and 2. Literature checked by web search on 2 Oct 2026; sources at the end.

## 0. Why the earlier answers sounded like two different things

Memo 1 used two axes without saying so.

- **The legs** are the process: variation, selection, retention. Campbell's VSR scheme, carried into organization theory by Aldrich and into economics by Nelson and Winter. I split selection into external (market, examiner, rivals) and internal (the firm pruning its own variants, Burgelman's internal selection environment). These say *what happens*.
- **The traditions** are the empirical schools that have measured parts of that process: industrial dynamics econometrics, organizational ecology and Red Queen, technology evolution on patent data, and renewal and abandonment models at the invention level. These say *who has done it and with what data*.

Crossing the two axes with the level of analysis gives one matrix. Everything you can do sits in a cell of it.

## 1. The consolidated framework

### 1A. The matrix: level by leg

Each cell names the measurable construct and the file on your disk that carries it. Blank cells are either unobservable or not yours to do.

| Level | Variation | External selection | Internal selection | Retention | Population structure |
|---|---|---|---|---|---|
| **Invention** (application, patent) | New filings; new-subclass filings; citation scope. PatEx, pre-grant, DISCERN | Grant vs rejection; rejection type; examiner leniency; market value. PatEx, Office Action, KPSS | Abandonment of pending applications; maintenance-fee lapse at each stage; sale by assignment. PatEx status, maintenance fees, assignments | Renewal to full term; self-citation and reuse. Maintenance fees, DISCERN citations | Density and age of the subclass the invention enters. PatentsView all assignees |
| **Routine or unit** (segment, inventor team, text) | Segment entry; new inventor teams; new business-description language. Segments, inventors, EDGAR Item 1 | Segment performance vs firm aspiration. Segments | Segment exit and divestiture; team dissolution. Segments, SDC M&A, inventors | Textual stability of Item 1 and MD&A; team persistence; segment persistence. EDGAR, inventors, Segments | Number of units; diversification. Segments, Diversification data |
| **Firm** | Search distance; R&D; alliance formation; acquisitions; strategic change. DISCERN, Compustat, SDC | Exit by merger, liquidation, or delisting; growth; market share; returns. CRSP delisting codes, Compustat, TNIC | Not observable except through the unit level above | Persistence of the firm's technological profile; knowledge-base breadth over time. DISCERN | Size and age distribution of the TNIC population; density; concentration. Compustat, TNIC |
| **Technology domain** (CPC subclass) | Entry of new assignees; breakthrough and novel patents. PatentsView, KPST | Domain decline and extinction; patent-value trend; CD index. PatentsView, KPSS, Funk and Owen-Smith CD data | Firm exit from the domain while the domain lives on. P023 spells | Domain survival in the firm's portfolio. P023 spells | Density, growth, age, concentration of the domain across all assignees. PatentsView |
| **Industry or population** | Entry rate; share of patents from new assignees. PatentsView, Compustat | Exit rate; share reallocation toward fitter firms; concentration. Compustat, CRSP, TNIC, KPSS | Not applicable | Persistence of heterogeneity; autocorrelation of profitability and productivity. Compustat | Technology-wave timing; AI exposure; discontinuity intensity. KPST, AIPD, Felten, CD index |

### 1B. Where the four traditions sit in the matrix

| Tradition | Cells it occupies | Its standard design | Its standard data | What it leaves out, which is your opening |
|---|---|---|---|---|
| Industrial dynamics econometrics, the Dosi and LEM school | Firm and population, external selection and retention | Growth-rate distributions; persistence of productivity differences; replicator-dynamics regressions of share growth on relative fitness | Census and national firm registers; Compustat | The firm is a passive carrier of fitness. No behavior between fitness and selection |
| Organizational ecology and Red Queen | Firm and population, external selection and population structure | Hazard models with density, age, size, niche width, competitive experience | Single-industry life histories; occasionally Compustat | The firm's response to feedback is inferred, not measured. Mostly single industries |
| Technology evolution on patents | Technology domain, variation and population structure | Niche crowding, local search, landscape ruggedness, CD index, breakthrough detection | USPTO patents, all assignees | Firm-level feedback is absent; the firm is a dot in technology space |
| Renewal and abandonment models | Invention, internal selection and retention | Option-value models of renewal; abandonment hazards | USPTO maintenance fees, PatEx | No behavioral trigger; the firm is a value-maximizing calculator |

Each tradition has one empty seat: the behavioral response that BTOF measures. That seat is the program. Every cell in 1A where you can put a feedback trigger on the left and a selection or retention outcome on the right is a paper nobody in these four traditions has written.

### 1C. The full list of studies, by cell

Codes refer to memo 2. New items here start with N8.

| Cell | Study | Status |
|---|---|---|
| Invention, variation to internal selection | A5 plus #2, gross vs pending vs net search | Ready |
| Invention, internal selection and retention | N3, pruning under pressure | Ready |
| Invention, external selection content | A6, diagnostic feedback; P025, unearned feedback | Ready, built |
| Invention, variation signal vs substance | A4, symbolic gap-closing | Partial data |
| Unit, internal selection | #7, shortfall localization | Ready, job talk |
| Unit, retention | N5, routine churn under vacillation | Ready, needs validation |
| Firm, variation to external selection | N1, does problemistic search save the firm | Ready |
| Firm, retention | N2, are problem-born explorations kept | Ready |
| Domain, variation and internal selection | A7, barbell reallocation; P023, domain exit | Ready, submitting |
| Domain, population structure | N4, density dependence of domain exit | Ready |
| Domain, external selection timing | N9, last to leave: exit timing relative to the domain's decline curve | Ready, new |
| Population, external selection with a behavioral mediator | N8, technological replacement and the search response, AI and earlier waves | Ready to 2021, new |
| Population, Red Queen | N6, Red Queen in technology space | Ready |
| Population, replicator dynamics | N7, does feedback-driven search speed market selection | Reservoir |
| Firm, variation via carriers | A1, A8, A10, #17 | Blocked on inventor tables |

## 2. Population-level work: what exists, and what you can do

### 2A. What has been done

**Technology replacing firms, economics.** This is where the volume is, and the firm is passive in all of it.

- Kogan, Papanikolaou, Seru and Stoffman 2017 QJE measure patent value from stock-market reactions and show that competitors' innovation output predicts a firm's lower growth and profits. Creative destruction at the firm-year level, Compustat and CRSP, 1926 to 2010. You hold the 2025 vintage of their data.
- Ma, NBER w29504, builds a firm-year measure of technological obsolescence from the citation decay of the patents a firm's knowledge base rests on. Obsolescence predicts lower growth, reallocation, and lower returns. It is explicitly a measure of being replaced.
- Acemoglu, Lelarge and Restrepo 2020 show, for French manufacturing, that robot adopters grow at the expense of non-adopting competitors, so industry employment falls while adopters expand. Replacement of non-adopters by adopters within a population.
- Babina, Fedyk, He and Hodson 2024 JFE measure AI investment from employee resumes. AI-investing firms grow in sales, employment and valuation, and industry concentration rises: winner-take-most.
- Sun and Trefler, NBER w29980, link AI patents to mobile-app parents and find that AI deployment raises app entry and exit, which they call creative destruction.
- Ma and Yang, Census CES-25-78, identify technology waves from patent novelty and show that at wave peaks a larger share of patents comes from new firms and concentration falls, then rises. Tech waves reallocate ideas between entrants and incumbents.
- Jovanovic and Rousseau on general purpose technologies: GPTs are adopted first by new firms, so GPT eras come with waves of entry and exit.

**Incumbents and discontinuities, management.** Rich in theory, thin in population-scale data.

- Eggers and Park 2018 Annals review incumbent adaptation to technological change and conclude the field has no holistic framework, only narrow explanations or over-complex contingency models.
- Klepper 1996 AER, Klepper and Simons 1997 ICC on technological extinctions, Suarez and Utterback 1995, Christensen, Suarez and Utterback 1998: dominant designs and shakeouts predict survival; adopting the dominant design more than doubles survival odds. Single industries, hand-collected histories.
- Bergek et al. 2013 RP: discontinuities often produce creative accumulation by incumbents rather than destruction.
- Rosenkopf and Tushman 1998 ICC: coevolution of community networks and technology in flight simulation.

**Ecology of technologies.** Almost empty.

- van den Oord and van Witteloostuijn 2017 PLOS ONE apply density dependence to biotechnology patents 1976 to 2003: a technology's density and diversity raise its growth; crowding and status lower it. One field, one paper, not in a management journal.
- Podolny and Stuart 1995 AJS on technological niches is the only widely cited precedent.
- Funk and Owen-Smith 2017 Management Science give the CD index, and Park, Leahey and Funk 2023 Nature show disruptiveness falling across all fields. Population-level trajectory measures exist and are public.

**Red Queen.** Barnett and Hansen 1996, Barnett and Pontikes 2008, Derfus et al. 2008. Search found no recent population-scale Red Queen study using patents or TNIC; the literature is mostly 1996 to 2010.

**Generative AI and firm dynamics, 2025 to 2026.** Entrepreneurship and labor so far: startups exposed to generative AI cut junior employment and churn more; exposed industries see about ten percent more entry after ChatGPT. Nothing yet on listed-incumbent exit, and nothing with a behavioral mediator.

### 2B. The gap, stated once

Economics has the exposure and the outcome, with the firm as a passive carrier. Management has the incumbent's response, in single industries and small samples. Ecology has selection, for firms not technologies. Nobody has run, at population scale across technologies and decades, the chain that your program is built to run: exposure to replacement, then the feedback it produces, then the search response or its absence, then survival. That chain is the evolutionary version of your whole paradigm.

### 2C. Can you do it with what is on disk? Yes, to 2021

**N8. Technological replacement and the search response.**

| Element | Operationalization | Data |
|---|---|---|
| Population | TNIC-3 industries, yearly, 1988 to 2021; SIC3 as the fallback back to 1980 | TNIC, Compustat |
| Replacement exposure, three measures | 1. Rivals' AI patent share and KPSS value in the firm's TNIC population, following Kogan et al. 2. Firm obsolescence following Ma: citation decay of the firm's cited-patent base. 3. Industry AI exposure from Felten as the exogenous shifter | AIPD, KPSS, DISCERN, PatentsView citations, Felten |
| Earlier waves | Define wave peaks per CPC domain from KPST breakthrough counts and the CD index, as Ma and Yang do, giving semiconductors, software and internet, biotech, and mobile as earlier replacement waves 1980 to 2021 | KPST, CD index |
| Feedback | Financial and innovation gaps as in your existing builds; the exposure should show up as a shortfall first | Compustat, DISCERN |
| Response | AI entry and share as in P024; search distance; exit from threatened domains as in P023 | AIPD, DISCERN, P023 spells |
| Outcome, firm | Exit by mode; growth; market share | CRSP delisting, Compustat |
| Outcome, population | Entry and exit rates; concentration; share reallocation toward adopters, the replicator coefficient | Compustat, TNIC, PatentsView new assignees |
| Identification | Exposure is industry-level and partly exogenous via Felten; the search response is where endogeneity lives. Use the examiner-leniency instrument for the innovation gap and the strict-examiner draw for the cost of responding, as in P025 | PatEx |

Predictions worth stating before building: exposure produces shortfall; shortfall produces search in some firms and not others, and the time structure of the shortfall, its duration and vacillation, predicts which; firms that respond with distant search survive at higher rates than non-responders in exposed populations only; at the population level, the replicator coefficient toward adopters is stronger where more incumbents respond. The last prediction is the one that makes it a population paper rather than a firm paper.

Suggested score: 3-4 / 2 / 2, so 13 to 16. The contribution is the mediator that all four traditions lack. The evidence score is capped by the endogeneity of the response.

**N9. Last to leave.** Within each declining CPC domain, the population has an exit curve. Where a firm sits on it, early or late, is a function of its feedback state. Predicted: shortfall accelerates exit from declining domains, surplus delays it, and persistent surplus produces the lock-in that ecology calls inertia and that Barnett and Pontikes call success bias. Ready from P023 spells plus PatentsView domain counts. Score 3 / 3 / 1, 13.

**N4, restated.** Density dependence of domain entry and exit, with feedback as the firm-level trigger. The van den Oord paper shows the shape exists in one field. Running it over all CPC subclasses and 1980 to 2021 with a behavioral trigger is new. Score 11 to 13.

### 2D. The limits, honestly

- **Listed firms only.** Births and small-firm deaths are invisible in Compustat. For N8 this matters because GPT eras are entry waves. Mitigation: count new assignees per domain in PatentsView as the entrant population, which includes private firms, and treat Compustat firms as the incumbent population. That is the split Ma and Yang use.
- **Compustat ends FY2021 locally.** The machine-learning wave of 2012 to 2021 is testable. The generative AI era after November 2022 is not, until WRDS access is settled. AIPD runs to 2023.
- **Exposure measures are proxies.** Rivals' AI patents are not AI deployment. Babina's resume measure and Acemoglu's robot purchases are closer to deployment. State this and triangulate with Felten.
- **Technology waves before 1988 lack TNIC.** Use SIC3 and accept the coarser population.

### 2E. Verdict on the two questions

Has population-level work on technologies replacing firms been done? Yes, in economics with passive firms, in management with small samples, and almost not at all as an ecology of technologies. Can you do it? Yes, through 2021, across four decades of waves, with the behavioral mediator that is missing everywhere else. It is the most ambitious paper the program can support, and it sits downstream of N1 and N2, which build its pieces.

## Sources consulted

- https://www.nber.org/papers/w17769 (Kogan, Papanikolaou, Seru, Stoffman)
- https://www.nber.org/papers/w29504 (Ma, Technological Obsolescence)
- https://www.bu.edu/econ/files/2020/01/competing_with_robots_nber.pdf (Acemoglu, Lelarge, Restrepo)
- https://ideas.repec.org/a/eee/jfinec/v151y2024ics0304405x2300185x.html (Babina, Fedyk, He, Hodson)
- https://www.nber.org/papers/w29980 (Sun, Trefler)
- https://www.census.gov/library/working-papers/2025/adrm/CES-WP-25-78.html (Ma, Yang)
- https://www.nber.org/system/files/working_papers/w11093/w11093.pdf (Jovanovic, Rousseau, GPTs)
- https://journals.aom.org/doi/10.5465/annals.2016.0051 (Eggers, Park)
- https://ideas.repec.org/a/oup/indcch/v6y1997i2p379-460.html (Klepper, Simons)
- https://acawiki.org/Strategies_for_survival_in_fast-changing_industries (Christensen, Suarez, Utterback)
- https://ideas.repec.org/a/eee/respol/v42y2013i6p1210-1224.html (Bergek et al.)
- https://faculty.wharton.upenn.edu/wp-content/uploads/2012/05/articrosenkopf_tushman_icc_1998.pdf (Rosenkopf, Tushman)
- https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0169961 (van den Oord, van Witteloostuijn)
- https://ideas.repec.org/a/eee/respol/v50y2021i1s0048733320301906.html and https://data.mendeley.com/datasets/j9z924hvfr (CD index)
- https://arxiv.org/pdf/2106.11184 (Park, Leahey, Funk)
- https://www.lem.sssup.it/WPLem/files/2017-06.pdf (Dosi, Pugliese, Santoleri)
- https://ideas.repec.org:443/a/oup/indcch/v28y2019i3p589-611..html (replicator dynamics in value chains)
- https://academicnewsletter.sufe.edu.cn/info/380578 and https://academicnewsletter.sufe.edu.cn/info/394386 (Barnett, Red Queen)
- https://fina.hkust.edu.hk/sites/finance/files/paper/Generative%20AI%20and%20Entrepreneurship.pdf and https://conference.nber.org/conf_papers/f238865.pdf (generative AI and entry)
- https://onlinelibrary.wiley.com/doi/10.1111/joms.13127 (Hudson 2026 JMS, industry AI exposure)
- https://www.nber.org/papers/w25266 (Kelly, Papanikolaou, Seru, Taddy)
