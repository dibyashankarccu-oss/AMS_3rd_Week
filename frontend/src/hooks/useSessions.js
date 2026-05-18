import { useState, useEffect } from "react";
import { sessionApi } from "../api/sessionApi";

export function useSessions() {

    const [sessions, setSessions] =
        useState([]);

    const [activities, setActivities] =
        useState([]);

    const [stats, setStats] =
        useState({});

    const [currentSession,
        setCurrentSession] =
        useState(null);

    const [search,
        setSearch] =
        useState("");

    const [moduleFilter,
        setModuleFilter] =
        useState("All");



    const refresh = () => {

        const allSessions =
            sessionApi
                .getSessions()
                .sort(
                    (a, b) =>
                        new Date(
                            b.loginTime
                        ) -
                        new Date(
                            a.loginTime
                        )
                );

        const allActivities =
            sessionApi
                .getActivities();

        setSessions(
            allSessions
        );

        setActivities(
            allActivities
        );

        setStats(
            sessionApi.stats()
        );

        setCurrentSession(
            sessionApi
                .getCurrentSession()
        );

    };



    useEffect(() => {

        refresh();

        const interval =
            setInterval(
                refresh,
                3000
            );

        window.addEventListener(
            "storage",
            refresh
        );

        return () => {

            clearInterval(
                interval
            );

            window.removeEventListener(
                "storage",
                refresh
            );

        };

    }, []);



    const filteredActivities =
        activities.filter(a => {

            const searchMatch =

                a.action
                    ?.toLowerCase()
                    .includes(
                        search
                            .toLowerCase()
                    )

                ||

                a.issueKey
                    ?.toLowerCase()
                    .includes(
                        search
                            .toLowerCase()
                    )

                ||

                a.module
                    ?.toLowerCase()
                    .includes(
                        search
                            .toLowerCase()
                    );



            const moduleMatch =

                moduleFilter ===
                    "All"

                    ?

                    true

                    :

                    a.module ===
                    moduleFilter;



            return (
                searchMatch &&
                moduleMatch
            );

        });



    const logout = (id) => {

        sessionApi.logout(
            id
        );

        refresh();

    };



    const logoutCurrent =
        () => {

            sessionApi
                .logoutCurrent();

            refresh();

        };



    return {

        sessions,

        activities:
            filteredActivities,

        stats,

        currentSession,

        search,

        setSearch,

        moduleFilter,

        setModuleFilter,

        refresh,

        logout,

        logoutCurrent,

        activeSessions:

            sessions.filter(
                s =>
                    s.status ===
                    "Active"
            ).length

    };

}