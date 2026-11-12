// Which day it is, in degrees (the same rule as My Audiobook Collection): 37° a day, so the
// whole app has one colour per day and takes a year to come back round. Loaded in the head,
// so the first paint is already in today's colours; a page left open turns at midnight.
window.dayTint = (when = new Date()) => (Math.floor(
  (when.getTime() - when.getTimezoneOffset() * 60000) / 86400000) * 37) % 360

const paintTheDay = () => document.documentElement.style.setProperty('--day', String(window.dayTint()))
paintTheDay()

const atMidnight = () => {
  const midnight = new Date()
  midnight.setHours(24, 0, 5, 0)
  setTimeout(() => { paintTheDay(); atMidnight() }, Math.max(1000, midnight.getTime() - Date.now()))
}
atMidnight()
