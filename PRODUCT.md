# Product

<!-- impeccable:product-schema 1 -->

## Platform

Windows desktop (native PySide6/Qt Quick; implemented in the current WSL environment).

## Stack

Python 3.12+, PySide6, Qt Quick/QML, dataclasses, and local JSON persistence, as specified in the user brief.

## Users

Torchlight: Infinite players who want to assemble and save equipment plans on a Windows desktop.

## Product Purpose

Torchlight Craft Planner is an offline item editor for selecting an equipment base, setting its item level and Priceless state, editing affixes, and saving equipment for later use. Success means the saved item can be reopened with its configuration intact.

## Positioning

The first release is a direct visual item editor that provides a persistent equipment workspace. Crafting probabilities, costs, and strategy simulation are explicitly outside this release.

## Operating Context

The app is designed for a desktop Windows workflow and should remain usable offline after installation. The initial reference season is SS14 — Tartarus; community data is not assumed to be verified for that season.

## Capabilities and Constraints

- v0.1 includes base selection, integer Item Level, a Priceless toggle, prefix/suffix selection and editing, and JSON save/load/duplicate/rename/delete.
- Affix catalog data stays separate from QML and includes source and verification status.
- Unknown compatibility and slot rules must remain visibly unverified rather than being presented as game rules.
- No crafting simulation, probabilities, material costs, OCR, game-process access, or automatic catalog updates.
- The requested distribution target is Windows x64. A Windows build cannot be produced from the current WSL session.
- The initial catalog is small and its community-source entries are pending SS14 verification.

## Brand Commitments

The supplied Torchlight: Infinite crafting screenshot is the visual reference. Interface labels use English, matching the screenshot.

## Evidence on Hand

The user supplied a crafting-screen screenshot and a detailed v0.1 specification. TLIDB is a fan-made community reference and labels its data as beta testing data; no official SS14 item-data confirmation is on hand.

## Product Principles

- Keep the item editor useful without a network connection.
- Preserve each saved item and its history-safe JSON representation.
- Make selection and editing changes visible immediately.
- Expose data uncertainty where it affects a choice.
- Keep v0.1 focused on editing and persistence.
