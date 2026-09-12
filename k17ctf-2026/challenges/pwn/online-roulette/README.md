# online-roulette

- **ID**: 33
- **Slug**: `online-roulette`
- **Category**: beginner,pwn
- **Difficulty**: beginner
- **Points**: 100  (152 solves)

## Description

live roulette players keep complaining that they dont get enough spins per hour, so we are introducing ROULETTE ONLINE!!! despite the (small) house edge, this minibolt guy keeps winning???

Note: We've added a debugging tool on the remote to help you out a bit.
The `SNAPSHOT()` call will [magically](https://man7.org/linux/man-pages/man2/ptrace.2.html) print out a view of the program stack.
You can ignore the snapshot stuff in the code, it's just there to enable this functionality.


Connection command: `nc chal.secso.cc 4000`

## Files

- `chal.c` (2,577 bytes) — sha256:180c99e65f25e87ec11a436aff9b8f9604b4cac4f1841d4e4a30ec97d9fd2865

## Submission

`input_type: text`
