# Document monthly execution snapshot hashing

Refs #9

## Target

cycles behavior in the pinned upstream source. [Source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/monthly-allocation.ts#L202-L256)

## Claim

Monthly execution snapshot construction hashes the serialized snapshot containing the nonzero award rows and their calculated fees.

## Evidence

The builder omits zero gross rows, computes gross, fee and net in integer units, and refuses a total above the cap. It records the source and manifest digests, allocation sequence and trigger, then hashes the JSON text returned beside the object. Historical reconstruction can select floor fee behavior. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/src/lib/payments/monthly-allocation.ts#L202-L256)

## Verification

Trace a zero row and a positive row through the loop. Check that only the positive row contributes to totalGrossBase and that the final hash is calculated over the returned text. The author checked the source statically. The example is a reviewer check.
