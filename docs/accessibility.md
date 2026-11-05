# Accessibility of the replay page

Checked on 2026-11-05 for the page this sample writes (`index.html` of an export). The checks are listed with their limits.
This is not a formal accessibility conformance evaluation.

## What was checked

- **Automated, axe-core 4.14.0** (WCAG 2.0/2.1/2.2 A and AA rules plus best practices) in Chrome, on an export of the
  synthetic walkthrough episode (one camera clip, one sealed finding), at desktop width, 320 CSS px and 400 % zoom:
  0 violations. Items axe could not decide: the arrow buttons (a symbol label; the accessible names are "Previous frame"
  and "Next frame", and the symbol measures 15.14:1 against its background) and one video without a caption track
  (see below).
- **Keyboard:** all 15 interactive elements are reachable with Tab and show a focus outline; Go to frame, Previous, Next,
  Play/Pause and the frame slider were operated with the keyboard. No horizontal scroll at 320 px or at 400 % zoom.
  This walk was scripted (Playwright), not done by a person.
- **VoiceOver on macOS with Chrome**, Tab path (before the slider and status-line changes below): buttons, the speed menu, the
  slider and the links were announced with name and role, and Space activated buttons. This run was made on the full Robot Reel project's page, which has the same
  controls and scripts; it was not repeated on this repository's page.

## Gaps and limits

- The camera clips are video-only recordings with no captions and no audio description. The values at each frame are
  available as text in the page and in `episode.json`.
- The chart canvases have no text alternative. Use the frame label, the slider and `episode.json`.
- A VoiceOver walk with the VoiceOver cursor over the page text and the charts was not done. NVDA, JAWS and TalkBack were
  not tested. The page does not respond to `prefers-reduced-motion`; playback starts only when you press Play.
- A VoiceOver run before the last two changes read the slider as a bare number and announced nothing after Previous or
  Next. The slider now has `aria-valuetext` ("Frame 10 of 26, 1.000 s") and Previous and Next write the new frame into the
  status line (`role="status"`). A static test checks that the text is set; VoiceOver was not run
  again after the change, so what a screen reader announces is unconfirmed. Announcement of Go to frame was not heard
  in that earlier run either.
