# Stable Rankings, Uncertain Attribution: Validating NBA Matchup Turnover Metrics

Anonymous submission

## Abstract

Public NBA matchup turnover rates are persistent, but persistence and aggregate reconciliation do not establish defender attribution or construct validity. Across eight regular seasons, we study these distinctions through a measurement audit and external validation. In 8,560 selected singleton-recoverable turnovers with an officially credited stealer or named offensive-foul drawer, the matchup assignment matches that contributor in 30.9% of events (Wilson 95% interval 29.9%–31.9%), although season totals differ from play-by-play by only +0.5% and -1.4%. A conservation identity explains why totals cannot validate individual assignments. A three-outcome model separates common engagement, turnover contrast, and foul-versus-shot mix. Turnover contrast has a stronger association with credited steals than adjusted turnover rate, including after adjustment for matchup shot volume. An exploratory next-season screen improves on adjusted turnover rate but is outperformed by prior credited steals. These results support a workflow for auditing a metric's meaning and intended use. They do not establish causal defensive credit, a population error rate, recovery of true rankings, or validated player-level uncertainty.

## 1. The decision problem

A staff using matchup turnover rates to compare defenders faces two distinct questions: are the recorded events assigned to the intended unit, and does the resulting rate represent the defensive activity of interest? Neither question is answered by finding that a leaderboard is stable.

Across the eight-season panel, the adjusted matchup turnover rate has median adjacent-season Spearman correlation 0.592. That is evidence of persistence. It does not establish whether the persistent signal represents ball disruption, opportunities, role, or their mixture. Franks et al. (2016) evaluate stability, discrimination, and independence as distinct properties of sports metrics. Tracking-based models already characterize multiple aspects of defense (Franks et al. 2015), and public matchup data have been used to describe defensive roles (Dubin 2018). Our question concerns a specific interpretation of the public turnover field: whether its recorded defender assignment supports using the resulting rate as a measure of disruption.

The contribution is an empirical measurement audit linking three levels of evidence: aggregate reconciliation, selected-event identity agreement, and external interpretation of season-level scores. The conservation identity explains why the first cannot substitute for the second. The outcome decomposition tests a possible interpretation of the persistent signal, while the exploratory screen establishes a practical limit by retaining the stronger simple predictor. Together these checks give a staff a concrete basis for deciding which claims a matchup metric can support.

## 2. Data, definitions, and audit population

The panel contains public NBA offender-defender matchup records for the 2017-18 through 2024-25 regular seasons. Each edge contains partial matchup possessions and feed-recorded turnovers, field-goal attempts, and shooting fouls. Partial possessions are the provider's exposure measure; they are not assumed to partition games into mutually exclusive plays. A matchup turnover means a turnover recorded on an edge, not a verified turnover caused by its defender. Throughout, "adjusted turnover rate" denotes the single-outcome rate after offensive-player and defensive-team adjustment, before the three-outcome decomposition; it is not the unadjusted turnover count divided by exposure. Appendix A specifies both estimators.

The archived loader queries the NBA Stats `boxscorematchupsv3` endpoint and flattens its nested player-matchup records. The hoopR and nba_api endpoint documentation independently list the relevant fields; these are client-maintainer schemas, not a specification of causal defensive credit. Appendix B records the operational mapping used here. Neither field names nor the present audit identify the provider's attribution rule, timing window, or allocation of shared responsibility.

Archived play-by-play for 2023-24 and 2024-25 supplies the reconciliation record. Team turnovers are excluded when comparing player turnover totals. Matchup files cover 1,227 and 1,229 games in the two seasons. Credited steals and blocks extracted from play-by-play across the panel serve as outcomes external to the joint model. These credits are official scoring records, not independent observations of causal defensive responsibility. Rates also share a partial-possession denominator with matchup measures.

For the event audit, a singleton-recoverable player-game has exactly one player turnover in play-by-play and exactly one matchup turnover on exactly one defender edge. Restricting to a credited stealer or named offensive-foul drawer yields 8,560 events. This is a selected, recoverable stratum. It excludes unresolved multi-turnover player-games and events without the required credit; it is not a random sample of NBA turnovers.

The comparison asks whether two records name the same person. A stealer may benefit from another defender's pressure, and a named foul drawer need not represent every contribution to the possession. Disagreement establishes that the two assignments are not interchangeable in this stratum. It does not by itself identify which assignment is appropriate for a different estimand.

## 3. Correct totals do not validate assignment

The same number of turnovers can be recorded while different defenders receive the assignments. Our selected-event comparison exposes a distinction that season totals conceal.

Season matchup totals differ from play-by-play player turnovers by +0.5% and -1.4%. Exact agreement within turnover-involved player-games is 68.5% and 68.2%. These are different statistics: the first is a signed relative discrepancy between totals, while the second is a proportion of player-games with identical counts. Neither is event-level defender accuracy.

Within the selected event audit, 2,644 of 8,560 matchup assignments match the credited contributor: 30.9%, with Wilson 95% interval 29.9%–31.9%. A game-cluster bootstrap gives a similar interval. The officially credited contributor appears on some matchup edge in 98.2% of these events, so most disagreement is not explained by that person's complete absence from the matchup record.

An exploratory breakdown using the original structured turnover subtype distinguishes where identity disagreement is concentrated. All selected events remain included.

| Recorded turnover subtype | Events | Matching identities | Agreement | Descriptive Wilson 95% interval |
|---|---:|---:|---:|---:|
| Bad pass | 4,256 | 683 | 16.0% | 15.0%–17.2% |
| Lost ball | 2,588 | 1,246 | 48.1% | 46.2%–50.1% |
| Offensive foul | 1,716 | 715 | 41.7% | 39.4%–44.0% |

These intervals do not account for game or player clustering. The differences describe this recoverable stratum, not all turnovers. They do not establish that the matchup defender pressured the passer, that the credited player merely received the ball, or that the provider records a particular phase of the possession. Official scoring can credit a controlled deflector even when a teammate gains possession (NBA Video Rulebook). The subtype result therefore identifies a validation question rather than a causal mechanism.

![Different validation checks](figures/figure1_measurement_checks.png)

Figure 1. Separate panels preserve each check's denominator. The aggregate panels use common games in each audit season; identity agreement uses only selected singleton-recoverable events with structured credit. The identity interval is Wilson, and it quantifies sampling variation within the selected stratum, not uncertainty about population transport or causal truth.

The inability of totals to establish assignment is algebraic. For a vector of counts within an offender-season group, consider a nonnegative column-stochastic receiver matrix R and an allocation operator

$$A(\epsilon,R)=(1-\epsilon)I+\epsilon R.$$

Because $\mathbf{1}^{\mathsf T}R=\mathbf{1}^{\mathsf T}$, we have $\mathbf{1}^{\mathsf T}A=\mathbf{1}^{\mathsf T}$. Every such redistribution preserves the group total. Preserving additional subgroup totals, such as totals within defensive teams, requires restricting redistribution within those subgroups. Many different defender assignments can therefore produce identical margins. This establishes a limitation of margin-based validation, not the provider's actual assignment algorithm.

For normalized edge shares r, the mean perturbation is $\epsilon(R-I)r$. Its magnitude depends on the receiver law as well as epsilon. Under stochastic reassignment, epsilon is the probability of entering the reassignment process. If reassignment can return to the original edge, the expected fraction of identities that actually change is $\epsilon\sum_j r_j(1-R_{jj})$, not epsilon itself. Neither quantity is automatically equal to a discrepancy between two observed records.

These identities distinguish reassignment scenarios from identification: forward perturbations describe sensitivity of the recorded data, while inversion of a mean relationship on sparse realized counts can produce negative estimates even under a valid stochastic process. Neither approach here identifies the provider's mechanism or bounds true player rankings.

## 4. What does the persistent score measure?

The turnover contrast is more closely associated with credited steals than the adjusted turnover rate, including after accounting for shot volume. The model helps interpret that difference by expressing each defender's recorded outcomes in three components.

Tracking-based defensive analysis distinguishes opportunities and context from outcomes (Franks et al. 2015). We use a simpler model suitable for the available public counts. For edge e and outcome k, the working log mean contains a log partial-possession offset plus outcome-specific intercept, offensive-player, defensive-team, and defender effects. Turnovers, field-goal attempts, and shooting fouls are modeled as overlapping count processes; their sum is not interpreted as mutually exclusive terminal opportunities.

The three fitted defender effects are expressed in an orthonormal basis: common engagement, turnover contrast, and foul-versus-shot contrast. Turnover contrast weights the turnover effect by $2/\sqrt{6}$ and each other outcome effect by $-1/\sqrt{6}$. This is a relative statistical contrast. It does not isolate causal disruption, effort, or overall value. Three outcome effects provide three coordinates; a fourth unrestricted trait would need additional information or identifying restrictions.

The external analyses use season-specific first-stage joint-model point estimates. They do not use future-smoothed dynamic scores. Dynamic simulation findings motivate caution about uncertainty but are not empirical player confidence intervals. Context adjustment, shrinkage, and prospective evaluation address different problems, consistent with the broader player-evaluation literature (Fearnhead and Taylor 2011; Sill 2010).

Across 3,367 eligible defender-seasons with at least 500 partial possessions, adjusted turnover rate correlates with credited steals at 0.100 and with credited blocks at 0.462. Turnover contrast correlates with those outcomes at 0.405 and -0.288, respectively. These associations alone do not establish a pure disruption construct. Credited blocks require shot opportunities, and shot counts are part of the fitted model.

After adjusting for matchup shot volume, adjusted turnover rate's correlation with credited steals rises to 0.210, while turnover contrast remains at 0.395. The contrast-block association attenuates to -0.046. We assign average ranks, regress each ranked variable on ranked field-goal attempts per 100 partial possessions and an intercept, and compute Pearson correlation between the residuals. This is the partial Spearman coefficient for the stated control. Re-ranking the residuals instead leaves the substantive interpretation unchanged in a sensitivity check. The observed block contrast is substantially related to shot volume. The more defensible positive evidence is the association with credited steals that remains after this adjustment. Correlations do not remove all role, scheme, or denominator dependence.

## 5. An exploratory screening application

The application asks whether prior-season rankings identify next-season credited-steal performance. It is not a test of recruitment success. For each adjacent-season transition, the historical cohort contains defenders changing main teams who reach 500 partial possessions in both seasons. The analysis comprises 808 player-transition pairs from 426 distinct defenders.

Each score selects exactly the ceiling of one-quarter of the cohort within transition using prior-season values. The target is membership in the equally sized top group by next-season credited steals per 100 partial possessions. Ties use stable row order; selection overlap is computed on individual row occurrences. The design conditions on observed team change and future participation; it was selected after the measurement investigation. Thus time ordering of the predictor does not make the entire study prospectively preregistered or remove cohort selection.

Top-quartile precision is 41.5% for turnover contrast and 26.3% for adjusted turnover rate. Their difference is 15.1 percentage points, with defender-cluster bootstrap 95% interval 6.2–23.6 over 2,000 resamples. Each resample draws whole defenders with replacement, preserving their observed trajectories, and recomputes both rankings within transition. Repeated copies are distinct sampled units: one copy entering the target group cannot confer membership on every copy of that player. The interval is percentile-based and conditional on the fitted scores and observed cohort design; it excludes full model-fitting, target-measurement, and design-selection uncertainty.

A cutoff-tie sensitivity allocates the exact selection quota fractionally among equal scores. Expected overlap assumes independent uniform tie-breaking for the two rankings. This leaves the point difference unchanged and gives a 95% interval of 6.2–23.4 percentage points. The substantive comparison does not depend on the evaluated tie conventions.

For context, uniform random selection of the same number of defenders within each transition has expected precision 25.4%. If transition t has n_t defenders and quota k_t = ceiling(n_t/4), expected overlap is k_t²/n_t; pooled expected precision is Σ_t(k_t²/n_t)/Σ_t k_t. The adjusted rate is numerically close to this reference. This comparison is descriptive, not a test of equivalence to chance.

The simplest relevant alternative is stronger: prior-season credited steals attain 64.9% on the same target. This is a legitimate predictor for the stated forecasting task, not a theoretical ceiling or an unfair comparison. The decomposition's value must therefore be argued as interpretation of a matchup measure, not superiority for forecasting credited steals.

A further exploratory pilot asks whether adding both model contrasts to prior steals and shooting-foul rate improves the same forecasting target. With expanding training windows and matched selection quotas, the expanded model attains 62.0%, compared with 64.1% for the simple fitted baseline. Appendix D reports all five test periods and the design limitations. This provides no demonstrated incremental forecasting benefit from the added components.

A separate finite sensitivity audit refits the season-specific models under stronger and weaker defender and team penalties and varies the single-outcome adjustment. The contrast retains its advantage over the rate comparator under every tested setting, while prior credited steals remain stronger. Exposure-adjusted associations and a separate count-target screen retain the same ordering. Appendix C reports the full evaluated set and distinguishes rate prediction from volume prediction; these checks do not quantify full model-fitting uncertainty.

The advantage over adjusted turnover rate is similar among non-changers and absent in the perimeter-role stratum. Those findings weaken acquisition-specific and general perimeter-disruption claims. Role strata use credited blocks as a proxy and should not be read as independent ground-truth positional labels. Exposure and participation checks address some alternative explanations but do not identify causal recruitment effects.

![External associations and forecasting comparison](figures/figure2_external_validation.png)

Figure 2. TO denotes turnover; the adjusted rate includes offensive-player and defensive-team adjustment. Left: associations before and after adjustment for matchup shot volume, using the same eligible defender-season set. Right: next-season top-quartile precision in the historical team-changing cohort, including prior credited steals as a simple alternative and the exact-quota random-selection expectation as a dashed reference. The reported bootstrap interval concerns the paired contrast-minus-rate difference, not separate uncertainty bars for every score.

## 6. A decision workflow for player comparisons

The concrete decision is whether the public matchup turnover field can serve as a proxy for credited individual disruption in a player comparison. The audit supplies evidence for qualifying that use; it does not choose which player to acquire.

| Analyst check | Evidence or question | Decision consequence |
|---|---|---|
| Define the intended quantity | Matchup assignment, official credit, and causal responsibility are different quantities | State which quantity the comparison requires before choosing a metric |
| Reconcile coverage and exposure | Align seasons, games, player turnovers and partial-possession definitions | Investigate discrepancies before interpreting rates; no universal discrepancy threshold is established |
| Check identity separately | Overall selected-event agreement is 30.9% despite close totals | Do not use aggregate reconciliation as evidence of interchangeable defender identities |
| Examine subtype | Bad-pass agreement is 16.0%, versus 48.1% for lost balls | Keep subtype visible in validation; do not infer pressure location or responsibility from the label |
| Test the intended use | Prior steals outperform the contrast; adding components does not improve the fitted simple baseline in the pilot | Retain a strong simple comparator and require evidence of benefit for each proposed predictive use |
| Record unresolved interpretation | Provider assignment rules and causal responsibility remain unidentified | Seek documentation or independent film evidence before turning the association into a skill claim |

For example, an analyst asked to rank defenders by "turnovers caused" might initially treat reconciled matchup totals as sufficient validation. The selected-event and subtype checks change that decision: the field can describe recorded matchup turnover activity, but the audit does not justify relabeling it as turnovers caused. If the requested target is next-season credited-steal rate, the tested simple alternatives are stronger. If the target is causal disruption, neither feed comparison nor the forecasting screen supplies the required labels.

The decomposition can add context about how recorded turnover, shot and foul effects combine. Engagement is a common fitted component, turnover contrast is relative to the other outcomes, and foul-versus-shot contrast is not a measure of discipline or foul cost. These coordinates can motivate questions; they cannot establish that a player benefits from teammates or scheme.

Subtype-specific film review is a proposed extension. A reviewer could examine how several defenders contribute to a bad-pass turnover without assuming that the matchup assignment or official credit identifies sole responsibility. Whether this workflow improves decisions or saves review time requires a fixed-budget comparison against simple review-selection rules on independently adjudicated cases. No staff-time saving, contract advantage, or cross-league performance is demonstrated here.

## 7. Limitations and independent review

The assignment audit is selected on recoverability and structured credit. Official credits can identify a contributor without identifying sole responsibility. Definitions can differ across records. External targets come from play-by-play but share exposure denominators with matchup rates, so they are not fully independent measurements. The models lack possession-level lineups, scheme, game-state, and garbage-time controls. The screening analysis is observational and post-specified, and participation selection remains consequential.

Independent human video validation was not available. The event audit compares structured records, so it supplies neither adjudicated defensive responsibility nor human inter-rater agreement. Film coding remains future evidence, not a promised submission result.

The empirical evidence covers one league and one public data product. The distinction between totals, assignment, and construct interpretation generalizes conceptually; the numerical results do not automatically transfer to other feeds or sports. No provider algorithm, population error rate, safe shortlist, causal acquisition effect, or calibrated player interval is identified.

## 8. Conclusion

The study establishes a concrete separation: season totals nearly reconcile while selected recoverable events often name different defenders. The conservation identity explains how those findings coexist. External credits clarify the persistent score's interpretation, and the stronger prior-steals predictor limits its forecasting role. Each check supports a different claim. A staff can use this distinction to decide what evidence is still needed before turning a matchup association into a player judgment.

## Reproducibility

All displayed empirical quantities and both figures are rendered from archived result files and separately versioned inference, sensitivity and exploratory pilot results through a single build script. The audit reproduces the archived screening point estimates and the previous adjusted-correlation calculations before applying occurrence-specific bootstrap matching and conventional partial rank correlation. Local verification records input hashes and numeric provenance. The sensitivity audit additionally refits the season-specific MAP models and checks baseline reproduction. A separate local data-to-result entry point reconstructs the assignment audit, aggregate reconciliation, season-specific scores, external credits, persistence and corrected inference from checksum-recorded research inputs, comparing results only after recomputation. It reuses the existing estimation functions and reproduces the checked headline results. A portable dependency subset was also extracted outside the project directory and rerun with verified data copies in a newly installed virtual environment, without system site packages. The checked aggregates reproduced and altered source or raw inputs were rejected. This is same-host execution verification, not an independent implementation, a new-machine test or replication of every supplementary analysis. A separate aggregate artifact package rebuilds the text and figures from the reported values; it does not re-estimate them from research data. The final submission requires a de-identified repository that documents data access, preprocessing, model estimation, and uncertainty calculations; a local portable source/data candidate is verified, and all required inputs were retrieved and hash-verified from upstream commit `e829d4678be1e075f99e5d41a1c5f97089be446b`; the public repository will provide these exact source links and retrieval instructions without re-hosting the records.

## Appendix A. Estimation and inference details

**Single-outcome comparison.** Within each season, the opponent's expected turnover rate for an offender-defender pair is estimated from that offender's other defender pairs, with 200 exposure units of shrinkage toward the overall season turnover rate. Subtracting expected from observed turnovers gives an assignment-adjusted residual. A defensive-team residual rate is then computed excluding the focal defender, with 1,000 exposure units in the denominator as shrinkage toward zero. The remaining residual is aggregated by defender and expressed per 100 partial possessions. A player's main team is the defensive team with greatest partial-possession exposure that season. These calculations do not use the following season's data.

**Joint estimator.** For outcome-specific linear predictor $\eta_{ek}$, the working objective is the Poisson negative log likelihood, up to count-only constants, plus Gaussian penalties:

$$\sum_{e,k}\{\exp(\eta_{ek})-y_{ek}\eta_{ek}\}
+\tfrac12\sum_{o,k}(\beta_{ok}/0.28)^2
+\tfrac12\sum_{t,k}(\gamma_{tk}/0.10)^2
+\tfrac12\sum_{d,j}(z_{dj}/s_j)^2,$$

where $\eta_{ek}=\log x_e+\alpha_k+\beta_{o(e),k}+\gamma_{t(e),k}+\theta_{d(e),k}$, $z_d=B\theta_d$, and $s=(0.22,0.18,0.15)$ in engagement, turnover-contrast, and foul-versus-shot order. These penalty scales are fixed implementation choices. Intercepts are unpenalized; the zero-centered penalties anchor effect location rather than imposing explicit sum-to-zero constraints. Team and defender separation can consequently depend on regularization where matchup support is weak. An orthonormal rotation identifies coordinates conditional on the fitted outcome effects, not independent causal traits.

Each season is fitted separately by L-BFGS-B with analytical gradients, relative function tolerance $10^{-8}$ and gradient tolerance $10^{-5}$. Archived diagnostics record convergence for every fitted season; the inference audit uses the archived point estimates rather than refitting the model. The Poisson objective is a working likelihood for overlapping outcome counts, so conditional independence is not asserted as a property of basketball events. The bootstrap below does not repair likelihood misspecification or uncertainty in fitted effects.

**Screening uncertainty.** The resampling unit is a defender's entire observed set of transitions. Every replicate draws the original number of distinct defenders with replacement and recomputes the within-transition predictor and outcome cutoffs. Different sampled copies of the same defender remain separate observations for selection and overlap. Percentile endpoints are the 2.5th and 97.5th percentiles of the paired precision differences. This resampling addresses repeated players; it does not resample seasons as a population of environments, refit the player models, or account for selecting the application after inspecting the data.

**Construct adjustment.** Tied observations receive average ranks. Ordinary least squares removes an intercept and the rank of matchup field-goal attempts per 100 partial possessions from both ranked variables. Pearson correlation of the two residual vectors gives the reported partial rank correlation. No hypothesis-test p-value is assigned to these descriptive associations.

## Appendix B. Operational data dictionary

The analysis uses the archived schema produced by `parse_boxscorematchupsv3_json` in the public nba_data loader. It retains the parent player and nested matchup player when flattening the endpoint response; the panel builder groups counts by game, offensive player, matchup defender, and defensive team. The following are analysis definitions, not inferred rules for how the provider identifies a defender.

| Archived field | Use in this study | Interpretation limit |
|---|---|---|
| `person_id`, `matchups_person_id` | Offensive-player and matchup-defender identifiers, respectively | An edge does not establish exclusive responsibility for an event |
| `partial_possessions` | Exposure offset and rate denominator | Not assumed to count disjoint terminal possessions |
| `matchup_turnovers` | Turnover count recorded on the edge | Not a direct count of turnovers caused by that defender |
| `matchup_field_goals_attempted`, `shooting_fouls` | Other two count outcomes in the joint model | Outcomes may overlap; their sum is not a possession partition |
| `team_id`, `home_team_id`, `away_team_id` | Defensive team is the game team opposite the parent player's team | Does not establish the five defenders present at event time |

The consulted hoopR schema uses the archived snake-case names; nba_api exposes fields including `personIdOff`, `personIdDef`, `partialPossessions`, and `matchupTurnovers`. Agreement in field coverage supports provenance tracing, not validation of the assignment mechanism. A historical provider specification or event-level tracking reconstruction would be needed to establish that mechanism. Official play-by-play credit is a separate comparison record, not a replacement definition silently imposed on the matchup feed.

## Appendix C. Model and exposure sensitivity

A separate post hoc audit refits each season under the original objective and then halves or doubles either the defender-component prior standard deviations or the defensive-team standard deviation, one family at a time. The offensive-player prior is held fixed. Smaller standard deviations imply stronger shrinkage. All fits start from the original initialization and use the original tolerances, with a maximum of 500 iterations. Baseline reproduction and optimizer convergence are checked before interpretation. This evaluates a finite set of penalty choices; it is not an uncertainty interval or a search for the best-performing model.

The single-outcome comparison separately halves or doubles both exposure pseudo-counts, or omits its team adjustment while retaining opponent adjustment. The table keeps the cohort and next-season credited-steal-rate target fixed. Joint-model scenarios change only the contrast predictor; single-outcome scenarios change only the adjusted-rate predictor. The prior credited-steal-rate comparison remains 64.9% throughout.

| Scenario | Adjusted-rate precision | Turnover-contrast precision |
|---|---|---|
| Baseline refit | 26.3% | 41.5% |
| Defender prior SDs × 0.5 | 26.3% | 42.4% |
| Defender prior SDs × 2 | 26.3% | 41.0% |
| Team prior SD × 0.5 | 26.3% | 40.5% |
| Team prior SD × 2 | 26.3% | 42.9% |
| Rate pseudo-counts × 0.5 | 25.9% | 41.5% |
| Rate pseudo-counts × 2 | 26.3% | 41.5% |
| Rate without team adjustment | 29.3% | 41.5% |

To examine exposure dependence, we also correlate each predictor with credited-steal counts after partial rank adjustment for partial possessions. The coefficients are 0.109 for the adjusted rate and 0.399 for turnover contrast. Using credited-steal rates and controlling for exposure yields 0.109 and 0.407, respectively. These descriptive checks use the existing eligible sample; controlling for exposure does not remove all shared measurement error or establish a replacement denominator.

Changing the screening target to next-season credited-steal counts gives precision of 14.6% for the adjusted rate and 42.0% for turnover contrast. Prior-season credited-steal counts yield 60.5%. This is an explicitly different target that reflects both opportunity and rate. It does not validate the original rate denominator, and it cannot be used interchangeably with the main screening result.

## Appendix D. Incremental screening pilot

This post hoc pilot retains the existing team-changing cohort and next-season top-quartile credited-steal-rate target. The first two transitions provide initial training; five subsequent transitions are evaluated with expanding windows that train the downstream classifier only on earlier transitions. Across these test periods there are 562 player-transition pairs and 142 selected slots in total, not per period. Players may recur. The smaller evaluation set differs from the full-cohort screen in Section 5.

Within each transition, prior-season features are transformed to average-rank percentiles, centered at 0.5 and multiplied by the square root of 12. Fixed ridge logistic models use prior steals alone, prior steals plus shooting-foul rate, or those two inputs plus turnover and foul-versus-shot contrasts. The objective is summed logistic negative log likelihood plus one-half the squared coefficient norm, excluding the intercept. The penalty is fixed at one with no tuning. L-BFGS-B fits use analytical gradients; all fits converge. Each method selects ceiling(n/4) cases with stable tie ordering. Both rates use partial possessions; shooting fouls are feed-recorded, not independently adjudicated foul cost.

| Predictor | Hits / selected slots | Precision | Mean next-season shooting fouls per 100 partial possessions | Brier score |
|---|---:|---:|---:|---:|
| Prior steals ranking | 90 / 142 | 63.4% | 1.637 | — |
| Fitted prior steals | 90 / 142 | 63.4% | 1.637 | 0.1238 |
| Fitted steals + shooting fouls | 91 / 142 | 64.1% | 1.566 | 0.1270 |
| Those inputs + both contrasts | 88 / 142 | 62.0% | 1.553 | 0.1276 |

Lower Brier score indicates better probability prediction. The expanded model's slightly lower selected shooting-foul rate does not establish an effective tradeoff or a causal reduction in fouls.

| Transition (season start years) | Training pairs | Test pairs | Quota | Prior-steals hits | Steals + fouls hits | Expanded hits |
|---|---:|---:|---:|---:|---:|---:|
| 2019–2020 | 246 | 119 | 30 | 19 | 18 | 19 |
| 2020–2021 | 365 | 122 | 31 | 20 | 20 | 19 |
| 2021–2022 | 487 | 107 | 27 | 21 | 21 | 19 |
| 2022–2023 | 594 | 116 | 29 | 14 | 15 | 14 |
| 2023–2024 | 710 | 98 | 25 | 16 | 17 | 17 |

The expanded model beats the steals-plus-fouls baseline in one period, ties one and loses three. Existing season-specific component estimates are reused, not refitted within the pilot. The analysis remains conditional on those estimates and on observed future participation and team change. The dataset was previously explored, so this is not a new independent holdout. Repeated players and five testing periods limit inference; no significance claim or universal exclusion of these features is warranted. Salary, roster availability, lineup fit, wins and review time are not evaluated. The pilot code, design amendment and aggregate results are stored separately from frozen inputs.

## References

Dubin, J. (2018, April 19; analysis with Krishna Narsu). [Nylon Calculus: Using NBA matchup data to define defensive roles](https://fansided.com/2018/04/19/nylon-calculus-nba-matchup-data-defensive-roles/). FanSided.

Fearnhead, P., and Taylor, B. M. (2011). On estimating the ability of NBA players. Journal of Quantitative Analysis in Sports, 7(3), Article 11.

Franks, A., D'Amour, A., Cervone, D., and Bornn, L. (2016). [Meta-analytics: Tools for understanding the statistical properties of sports metrics](https://arxiv.org/abs/1609.09830). arXiv:1609.09830.

Franks, A., Miller, A., Bornn, L., and Goldsberry, K. (2015). [Characterizing the spatial structure of defensive skill in professional basketball](https://doi.org/10.1214/14-AOAS799). Annals of Applied Statistics, 9(1), 94–121.

Sill, J. (2010). Improved NBA adjusted plus-minus using regularization and out-of-sample testing. MIT Sloan Sports Analytics Conference.

Data and software documentation (accessed September 6, 2026): [nba_data archive and loader](https://github.com/shufinskiy/nba_data); [hoopR: nba_boxscorematchupsv3](https://search.r-project.org/CRAN/refmans/hoopR/html/nba_boxscorematchupsv3.html); [nba_api: BoxScoreMatchupsV3](https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/boxscorematchupsv3.md). These document data access and schemas; they are not evidence of causal attribution.

NBA Video Rulebook. [Steal, credited to defender who deflects the ball away from opponent](https://videorulebook.nba.com/archive/steal-credited-to-defender-who-deflects-the-ball-away-from-opponent/). Accessed September 12, 2026.
