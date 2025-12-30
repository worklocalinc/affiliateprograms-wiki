import { useEffect, useState } from "react";

interface TocItem {
  id: string;
  label: string;
  level: number;
}

interface TableOfContentsProps {
  items: TocItem[];
}

export function TableOfContents({ items }: TableOfContentsProps) {
  const [activeId, setActiveId] = useState<string>("");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      { rootMargin: "-80px 0px -80% 0px" }
    );

    items.forEach((item) => {
      const element = document.getElementById(item.id);
      if (element) observer.observe(element);
    });

    return () => observer.disconnect();
  }, [items]);

  return (
    <nav className="sticky top-20">
      <h4 className="font-medium text-foreground mb-3 text-sm">On this page</h4>
      <div className="border-l border-border">
        {items.map((item) => (
          <a
            key={item.id}
            href={`#${item.id}`}
            className={`toc-link ${activeId === item.id ? "toc-link-active" : ""}`}
            style={{ paddingLeft: `${12 + (item.level - 1) * 12}px` }}
          >
            {item.label}
          </a>
        ))}
      </div>
    </nav>
  );
}
