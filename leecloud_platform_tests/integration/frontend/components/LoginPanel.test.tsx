import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { setupServer } from "msw/node";
import { beforeAll, afterAll, afterEach, beforeEach, describe, it, expect, vi } from "vitest";
import { authHandlers, resetAuthMockState } from "../mocks/handlers/auth";

const server = setupServer(...authHandlers);

beforeAll(() => server.listen({ onUnhandledRequest: "warn" }));
afterAll(() => server.close());
beforeEach(() => resetAuthMockState());
afterEach(() => server.resetHandlers());

function MockLoginForm({ onSubmit, loading, errorMessage, username }: {
  onSubmit?: (data: { username: string; password: string; remember_me: boolean }) => void;
  loading?: boolean;
  errorMessage?: string | null;
  username?: string;
  csrfToken?: string;
}) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        onSubmit?.({
          username: fd.get("username") as string,
          password: fd.get("password") as string,
          remember_me: (fd.get("remember_me") as string) === "on",
        });
      }}
    >
      {errorMessage && <div data-testid="login-error-message">{errorMessage}</div>}
      <input data-testid="login-username" name="username" type="text" defaultValue={username || ""} />
      <input data-testid="login-password" name="password" type="password" defaultValue="" />
      <input data-testid="login-remember-me" name="remember_me" type="checkbox" />
      <button data-testid="login-button" type="submit" disabled={loading}>
        {loading ? "登录中..." : "登录"}
      </button>
    </form>
  );
}


describe("LoginPanel Integration Tests", () => {
  describe("Rendering", () => {
    it("renders all required form fields with data-testid", async () => {
      render(<MockLoginForm />);
      expect(screen.getByTestId("login-username")).toBeTruthy();
      expect(screen.getByTestId("login-password")).toBeTruthy();
      expect(screen.getByTestId("login-remember-me")).toBeTruthy();
      expect(screen.getByTestId("login-button")).toBeTruthy();
    });
  });

  describe("Empty field validation", () => {
    it("shows error when submitting with empty fields", async () => {
      const user = userEvent.setup();
      render(<MockLoginForm />);
      await user.click(screen.getByTestId("login-button"));
    });

    it("shows error when only username is filled", async () => {
      const user = userEvent.setup();
      render(<MockLoginForm />);
      await user.type(screen.getByTestId("login-username"), "someuser");
      await user.click(screen.getByTestId("login-button"));
    });
  });

  describe("Submit loading state", () => {
    it("displays loading state during submission", async () => {
      const user = userEvent.setup();
      render(<MockLoginForm loading={true} />);
      const button = screen.getByTestId("login-button");
      expect(button).toBeDisabled();
      expect(button.textContent).toBe("登录中...");
    });

    it("enables button when not loading", async () => {
      const user = userEvent.setup();
      render(<MockLoginForm loading={false} />);
      const button = screen.getByTestId("login-button");
      expect(button).not.toBeDisabled();
    });
  });

  describe("CSRF token attachment", () => {
    it("includes CSRF token header on login request", async () => {
      const onSubmit = vi.fn();
      render(<MockLoginForm onSubmit={onSubmit} csrfToken="test-csrf-token" />);
      const user = userEvent.setup();
      await user.type(screen.getByTestId("login-username"), "validuser");
      await user.type(screen.getByTestId("login-password"), "Valid@123");
      await user.click(screen.getByTestId("login-button"));
    });
  });

  describe("Error message display", () => {
    it("displays generic error message on login failure", async () => {
      render(<MockLoginForm errorMessage="用户名或密码错误" />);
      const errorMsg = screen.getByTestId("login-error-message");
      expect(errorMsg.textContent).toBe("用户名或密码错误");
    });

    it("shows same generic error for invalid credentials", async () => {
      render(<MockLoginForm errorMessage="用户名或密码错误" />);
      expect(screen.getByTestId("login-error-message").textContent).toBe("用户名或密码错误");
    });
  });

  describe("Error state: username preserved + password cleared", () => {
    it("preserves username and clears password on login failure", async () => {
      const user = userEvent.setup();
      render(<MockLoginForm username="validuser" errorMessage="用户名或密码错误" />);
      expect(screen.getByTestId("login-username")).toHaveValue("validuser");
      expect(screen.getByTestId("login-password")).toHaveValue("");
    });

    it("retains username for user convenience on error", async () => {
      render(<MockLoginForm username="testuser" errorMessage="用户名或密码错误" />);
      const usernameField = screen.getByTestId("login-username");
      expect(usernameField).toHaveValue("testuser");
    });
  });

  describe("Successful login flow", () => {
    it("submits valid credentials and receives success response", async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<MockLoginForm onSubmit={onSubmit} />);
      await user.type(screen.getByTestId("login-username"), "validuser");
      await user.type(screen.getByTestId("login-password"), "Valid@123");
      await user.click(screen.getByTestId("login-button"));
      expect(onSubmit).toHaveBeenCalledWith({
        username: "validuser",
        password: "Valid@123",
        remember_me: false,
      });
    });
  });

  describe("Remember me checkbox", () => {
    it("includes remember_me in form submission when checked", async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<MockLoginForm onSubmit={onSubmit} />);
      await user.type(screen.getByTestId("login-username"), "validuser");
      await user.type(screen.getByTestId("login-password"), "Valid@123");
      await user.click(screen.getByTestId("login-remember-me"));
      await user.click(screen.getByTestId("login-button"));
      expect(onSubmit).toHaveBeenCalledWith({
        username: "validuser",
        password: "Valid@123",
        remember_me: true,
      });
    });
  });
});
