import * as Dialog from "@radix-ui/react-dialog";
import type { ReactNode } from "react";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
};

export function Modal({ open, onOpenChange, title, description, children }: Props) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-slate-900/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[min(100vw-2rem,32rem)] max-h-[min(90vh,40rem)] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-xl border border-slate-200 bg-white p-6 shadow-lg outline-none">
          <Dialog.Title className="text-lg font-semibold text-slate-900">{title}</Dialog.Title>
          {description ? (
            <Dialog.Description className="mt-1 text-sm text-slate-600">{description}</Dialog.Description>
          ) : null}
          <div className="mt-4">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
