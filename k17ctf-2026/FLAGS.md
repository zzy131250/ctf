# k17ctf flag 清单

> 赛后整理（2026-09-12）。其中 blowfish / close enough 两题，服务端自己吐出来的前缀是
> `SCONES{...}` 而不是 `K17{...}` —— 多半是出题人从上一个 CTF 复用了代码没换 flag。

## 已解（26）

| # | 题目 | 分类 | Flag |
|---|------|------|------|
| 3 | DriveOne | web | `K17{i'm_to0_la2y_t0_wr1t3_a_pr0p3r_fl@g_anyway$_congr@ts}` |
| 4 | Duplex | web | `K17{un4_p3t1t10_dupl3x_53n5u5...}` |
| 7 | polynomial evaluator | web | `K17{P4553D_JQU3RY_4ND_J5_4T_TH3_54M3_TIM3!}` |
| 9 | blowfish | crypto | `SCONES{great_work_infiltrating_as_the_head_fish_perhaps_one_could_call_you_james_pond}` |
| 10 | cry-pto | crypto | `K17{y0u_ar3_f1ll3d_wth_deter1min4t10n}` |
| 11 | cryjail | crypto | `K17{yaaaaaaay_i_h0pE_yoU_D1dn7_cra5H_0Ut!!!!!!!!!!!}` |
| 12 | leaky rsa | crypto | `K17{th3_t1tan1c_sh0uldv3_us3d_duct_t4p3}` |
| 13 | shamir secret spilling | crypto | `K17{0ur_cl1ent5_r3ally_d0nt_like_r0tating_their_keys!}` |
| 15 | sanity check | meta | `K17{w3lc0me_t0_k17_1n_th3_b1g_26}` |
| 16 | archive trap | misc | `K17{n0t_so_s3cr3t_4rchive}` |
| 17 | close enough | forensics | `SCONES{y0u_got_m3_out_of_a_p1ckle}` |
| 18 | P = NP | misc | `K17{i_have_discovered_a_truly_marvellous_flag_which_this_box_is_too_simple_to_contain}` |
| 19 | verify you are human | misc | `K17{ABABBABAABBBAAAA}` |
| 22 | sudo but good | misc | `K17{ju$t_d0n't_writ3_bugs_ezpz}` |
| 23 | get fixed boi | forensics | `K17{cr1ms0n_0r_corrup73d}` |
| 24 | larpfest | osint | `K17{l00k_im_a_1337_h4x0r}` |
| 25 | rainier | osint | `K17{Victoria,Middle}` |
| 26 | big-win | pwn | `K17{maybe_the_true_reward_is_the_stacks_we_pwned_along_the_way}` |
| 27 | huge binary 1 | pwn | `K17{it's_ab0v3_aver@ge_actua1ly}` |
| 30 | java notes | pwn | `K17{i_am_java_ONE_with_java!!!!oashd8aghrdfo8aehFIOEASDJFNLC}` |
| 31 | make-a-wish | pwn | `K17{my_f4v0ur1t3_fl4v0ur_15_k1w1_p1n34ppl3_btw}` |
| 33 | online-roulette | pwn | `K17{th1s_minib0lt_guy_must_b3_rlly_lucky_huh}` |
| 35 | etch-a-sketch | rev | `K17{my_masterpiece}` |
| 36 | Evilgram | rev | `K17{y0u_Th0ug5t_W3_w3Re_Ev1l_bUt_re4llY_we_are_JuSt_m4ss1ve_cH1ck3n_l0v3rs_w1th_a_huge_Hung3r_anD_n0th1ng_cAn_sT4nd_1n_OuR_way!!}` |
| 37 | monoid | rev | `K17{a_M0NaD_1s_4_M0n0Id_1n_th3_c4t3gORy_0f_3Nd0FuNC70r5}` |
| 39 | srev | rev | `K17{00p$_nO_s1g$}` |

## 未解 —— 卡在"要你开实例"（instantiator 不认 team token）

| # | 题目 | 分类 | 说明 |
|---|------|------|------|
| 6 | macrohard azuer | web | Instantiator |
| 8 | whatsNew | web | Instantiator |
| 20 | prime calc | misc | Instantiator（题面还提示"对机器差异敏感"） |
| 21 | spot | misc | Instantiator |

## 未解 —— 这台机器网络打不到

| # | 题目 | 说明 |
|---|------|------|
| 5 | edwalk | `*.workers.dev`，DNS 污染 + SNI 阻断 |
| 38 | reverse captcha | 同上 |

## 未解 —— 需要你自己操作

| # | 题目 | 说明 |
|---|------|------|
| 14 | discord | flag 在赞助商频道，要你进 Discord 取 |

## 未解 —— 可以直连、还没打完

| # | 题目 | 远端 |
|---|------|------|
| 28 | huge binary 2 | `nc chal.secso.cc 4005` |
| 29 | ihyh | `nc chal.secso.cc 4007` |
| 32 | not json | `nc chal.secso.cc 4003` |
| 34 | waf | `nc chal.secso.cc 4006` |

每道题的解法见对应题目目录下的 `WRITEUP.md`（没有写的说明还没解或是一句话题）。
