exports.createSchemaCustomization = ({ actions }) => {
  const { createTypes } = actions;
  const typeDefs = `
    type ActivitiesJson implements Node @dontInfer {
      id: String
      distance: Float
      name: String
      run_id: Float
      moving_time: String
      type: String
      average_speed: Float
      average_heartrate: Float
      location_country: String
      start_date: Date
      start_date_local: Date
      streak: Float
      summary_polyline: String
    }
  `;
  createTypes(typeDefs);
};
