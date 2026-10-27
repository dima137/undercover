import { expect, it } from "vitest";
import { formatDollars, humanize, messageOf, stateLabel } from "./format";

it("formats money in US dollars", () => {
  expect(formatDollars(1250)).toBe("$1,250.00");
  expect(formatDollars(420.5)).toBe("$420.50");
});

it("names each state", () => {
  expect(stateLabel("in_progress")).toBe("In progress");
  expect(stateLabel("waiting_for_sign_off")).toBe("Waiting for sign-off");
});

it("turns a code word into a sentence", () => {
  expect(humanize("trip_delay")).toBe("Trip delay");
});

it("reads the message from an error", () => {
  expect(messageOf(new Error("Busy"))).toBe("Busy");
  expect(messageOf("odd")).toBe("Something went wrong");
});
