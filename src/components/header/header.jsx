import React, { Fragment } from "react";
import { Link, StaticQuery, graphql } from "gatsby";

const Header = ({ siteTitle }) => (
  <StaticQuery
    query={graphql`
      query AvatarQuery {
        avatar: allImageSharp

        {
          edges {
            node {
              image: fluid(srcSetBreakpoints: [32, 64, 96], quality: 85) {
                srcSet
                srcSetWebp
                base64
              }
            }
          }
        }
      }
    `}
    render={(data) => (
      <Fragment>
        <nav className="db flex justify-between w-100 pa3 ph5-l">
          <div className="dib w-25 v-mid">
            <Link to="/" className="link dim">
              <picture>
                <source
                  srcSet={data.avatar.edges[0].node.image.srcSet}
                  type="image/jpeg"
                />
                <source
                  srcSet={data.avatar.edges[0].node.image.srcSetWebp}
                  type="image/webp"
                />
                <img
                  className="dib w2 h2 br-100"
                  alt={siteTitle}
                  src={data.avatar.edges[0].node.image.base64}
                />
              </picture>
            </Link>
          </div>
        </nav>
      </Fragment>
    )}
  />
);

export default Header;
