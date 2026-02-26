export function createAdminAppReturn(sections) {
  return {
    ...sections.stateSection,
    ...sections.derivedSection,
    ...sections.serviceSection,
    ...sections.loaderSection,
    ...sections.sessionSection,
    ...sections.displaySection,
    ...sections.regionSection,
    ...sections.jobSection,
    ...sections.accountSection,
    ...sections.fetchSection,
    ...sections.resetSection,
    ...sections.applicationSection,
    ...sections.interviewSection,
    ...sections.detailSection,
  };
}
