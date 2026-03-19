"use client";

import React, { useState, useEffect } from "react";
import {
  DndContext,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
  useDroppable,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { maintenanceAPI } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { WrenchScrewdriverIcon, PlusIcon, CalendarIcon, ChevronRightIcon } from "@heroicons/react/24/outline";

const COLUMNS = [
  { id: "todo", title: "To Do", bg: "bg-slate-50 dark:bg-slate-800/50" },
  { id: "in_progress", title: "In Progress", bg: "bg-orange-50/50 dark:bg-orange-900/10" },
  { id: "completed", title: "Completed", bg: "bg-emerald-50/50 dark:bg-emerald-900/10" },
];

function SortableItem({ log, isOverlay }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: log.id, data: log });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
    cursor: isDragging ? "grabbing" : "grab",
  };

  const priorityColor =
    log.priority === "urgent" ? "bg-red-500" :
    log.priority === "high" ? "bg-orange-500" :
    log.priority === "medium" ? "bg-blue-500" : "bg-slate-400";

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`card p-4 relative overflow-hidden transition-shadow shadow-sm hover:shadow active:shadow-md mb-3 ${isOverlay ? "scale-105 shadow-xl rotate-2 ring-2 ring-brand-500 cursor-grabbing" : ""}`}
    >
      <div className={`absolute top-0 left-0 bottom-0 w-1 ${priorityColor}`}></div>
      <div className="pl-2">
        <h4 className="text-sm font-semibold text-slate-900 dark:text-white mb-1 line-clamp-2">
          {log.description}
        </h4>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-slate-500 font-medium">#{log.id.split("-")[0]}</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 capitalize">{log.maintenance_type}</span>
        </div>
        <div className="border-t border-slate-100 dark:border-slate-800 pt-3 flex items-center justify-between text-xs">
          <span className="text-slate-500 font-medium flex items-center gap-1">
            <WrenchScrewdriverIcon className="h-3 w-3" />
            {log.equipment_name || "Unknown Asset"}
          </span>
          {log.priority === "urgent" && (
            <span className="flex items-center gap-1 text-red-600 font-bold uppercase tracking-wider text-[10px]">
              <span className="h-1.5 w-1.5 rounded-full bg-red-600 animate-pulse"></span> Urgent
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function Column({ col, items }) {
  const { isOver, setNodeRef } = useDroppable({
    id: col.id,
  });

  return (
    <div ref={setNodeRef} className={`flex flex-col flex-1 min-w-[300px] h-[700px] rounded-2xl ${col.bg} border ${isOver ? 'border-brand-500 shadow-sm' : 'border-slate-200/50 dark:border-slate-700/50'} transition-all`}>
      <div className="p-4 border-b border-slate-200/50 dark:border-slate-700/50 flex items-center justify-between">
        <h3 className="font-semibold text-sm text-slate-800 dark:text-slate-200 flex items-center gap-2">
          {col.title}
          <span className="flex items-center justify-center h-5 w-5 rounded-full bg-slate-200 dark:bg-slate-700 text-xs font-bold text-slate-600 dark:text-slate-400">
            {items.length}
          </span>
        </h3>
        <button className="text-slate-400 hover:text-brand-500 transition-colors">
          <PlusIcon className="h-4 w-4" />
        </button>
      </div>
      <div className="p-3 flex-1 overflow-y-auto">
        <SortableContext items={items.map((i) => i.id)} strategy={verticalListSortingStrategy}>
          {items.map((log) => (
            <SortableItem key={log.id} log={log} />
          ))}
        </SortableContext>
      </div>
    </div>
  );
}

export default function KanbanBoard() {
  const [logs, setLogs] = useState([]);
  const [activeId, setActiveId] = useState(null);
  
  useEffect(() => {
    maintenanceAPI.list({ page_size: 100 }).then(({ data }) => {
      setLogs(data.items || []);
    });
  }, []);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor)
  );

  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  const handleDragOver = (event) => {
    const { active, over } = event;
    if (!over) return;
    
    // We only change columns loosely during over, but actual DB update happens on dragEnd
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;
    setActiveId(null);
    if (!over) return;

    const activeLog = logs.find(l => l.id === active.id);
    const overId = over.id; // Could be a column ID or another item ID

    let targetColumn = COLUMNS.find(c => c.id === overId)?.id;
    if (!targetColumn) {
      // Find the item it was dropped over to determine the column
      const overLog = logs.find(l => l.id === overId);
      if (overLog) targetColumn = overLog.status;
    }

    if (targetColumn && activeLog.status !== targetColumn) {
      // Optimistic update
      setLogs(logs.map(log => 
        log.id === active.id ? { ...log, status: targetColumn } : log
      ));

      try {
        await maintenanceAPI.update(active.id, { status: targetColumn });
      } catch (e) {
        // Revert on failure
        setLogs(logs.map(log => 
          log.id === active.id ? { ...log, status: activeLog.status } : log
        ));
      }
    }
  };

  const getLogsForColumn = (columnId) => {
    return logs.filter(log => (log.status || "todo") === columnId);
  };

  return (
    <div className="w-full">
      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-xl font-bold tracking-tight text-slate-800 dark:text-slate-100 flex items-center gap-2">
          <CalendarIcon className="h-6 w-6 text-brand-500" /> Maintenance Backlog
        </h2>
      </div>
      
      <DndContext 
        sensors={sensors} 
        collisionDetection={closestCorners} 
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-6 overflow-x-auto pb-4">
          {COLUMNS.map((col) => (
            <Column key={col.id} col={col} items={getLogsForColumn(col.id)} />
          ))}
        </div>
        
        <DragOverlay>
          {activeId ? <SortableItem log={logs.find(l => l.id === activeId)} isOverlay /> : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}
